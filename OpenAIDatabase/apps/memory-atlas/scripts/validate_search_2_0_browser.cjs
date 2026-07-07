#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const outputDir = getArg("--output-dir") || fs.mkdtempSync(path.join(os.tmpdir(), "search-2-0-browser-"));
const targetUrl = getArg("--url") || "http://127.0.0.1:5173/";
const browserExecutable = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || findChromiumExecutable();
const checks = [];

const runtimeVersion = "search_2_0_runtime.v1_1_7_stage7_phase1";
const sessionSummaryVersion = "search_2_0_session_summary.v1_1_7_stage7_phase1";

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

async function openSearch(page) {
  await page.goto(targetUrl, { waitUntil: "networkidle", timeout: 30_000 });
  await page.locator('[data-nav-view="search"]').click({ timeout: 10_000 });
  await page.waitForSelector(`[data-search-2-0-runtime="${runtimeVersion}"]`, { timeout: 30_000 });
}

async function fillSearch(page, query) {
  const input = page.locator("[data-search-query-input]");
  await input.fill(query);
  await page.waitForTimeout(250);
}

async function firstResultSnapshot(page) {
  return page.evaluate(() => {
    const root = document.querySelector("[data-search-2-0-runtime]");
    const result = root?.querySelector("[data-search-result]");
    const text = root?.textContent || "";
    const actions = [...(result?.querySelectorAll("[data-search-jump]") || [])].map((node) =>
      node.getAttribute("data-search-jump"),
    );
    return {
      rootVersion: root?.getAttribute("data-search-2-0-runtime") || null,
      summaryVersion: root?.querySelector("[data-search-session-summary]")?.getAttribute("data-search-session-summary") || null,
      resultCount: root?.querySelectorAll("[data-search-result]").length || 0,
      resultId: result?.getAttribute("data-result-id") || null,
      matchedReason: result?.getAttribute("data-matched-reason") || "",
      evidenceRef: result?.getAttribute("data-evidence-ref") || "",
      proposalCandidate: result?.getAttribute("data-proposal-candidate") || "",
      actionKinds: actions,
      hasMatchedReasonText: text.includes("matched_reason"),
      hasEvidenceRefsText: text.includes("evidence_refs"),
      hasProposalCandidateText: text.includes("proposal_candidate"),
      textSample: text.slice(0, 360),
    };
  });
}

async function main() {
  fs.mkdirSync(outputDir, { recursive: true });
  const { chromium } = requirePlaywright();
  const browser = await chromium.launch({
    executablePath: browserExecutable,
    headless: true,
    args: ["--disable-dev-shm-usage"],
  });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
  const page = await context.newPage();
  const consoleMessages = [];
  const failedResponses = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleMessages.push(message.text());
  });
  page.on("response", (response) => {
    if (response.status() >= 400) failedResponses.push({ status: response.status(), url: response.url() });
  });
  await page.route("**/__memory_atlas_runtime_state", (route) => route.fulfill({ status: 204, body: "" }));
  await page.route("**/__memory_atlas_heartbeat", (route) => route.fulfill({ status: 204, body: "" }));
  await page.route("**/__memory_atlas_release", (route) => route.fulfill({ status: 204, body: "" }));

  try {
    await openSearch(page);
    const root = await page.evaluate(() => {
      const element = document.querySelector("[data-search-2-0-runtime]");
      return {
        runtimeVersion: element?.getAttribute("data-search-2-0-runtime") || null,
        filterState: Boolean(element?.querySelector("[data-search-filter-state]")),
        sessionSummary: element?.querySelector("[data-search-session-summary]")?.getAttribute("data-search-session-summary") || null,
      };
    });
    assertCondition(
      root.runtimeVersion === runtimeVersion &&
        root.filterState === true &&
        root.sessionSummary === sessionSummaryVersion,
      "stage7_phase1_browser_runtime_root",
      "Search 2.0 runtime root exposes versioned root, filter state and session summary",
      "Search 2.0 runtime root is incomplete",
      root,
    );

    await fillSearch(page, "Codex");
    await page.waitForSelector("[data-search-result]", { timeout: 10_000 });
    const result = await firstResultSnapshot(page);
    assertCondition(
      result.resultCount > 0 &&
        Boolean(result.resultId) &&
        result.matchedReason.length > 12 &&
        result.evidenceRef.length > 0 &&
        result.actionKinds.includes("starfield") &&
        result.actionKinds.includes("river") &&
        result.actionKinds.includes("inspector") &&
        result.hasMatchedReasonText === true &&
        result.hasEvidenceRefsText === true &&
        result.hasProposalCandidateText === true,
      "stage7_phase1_browser_result_fields",
      "Search result exposes matched reason, evidence refs, proposal flag and three jump actions",
      "Search result fields or actions are incomplete",
      result,
    );

    const debugSignal = await page.evaluate(() => window.__memoryAtlasStage7Phase1?.() ?? null);
    assertCondition(
      debugSignal?.runtimeVersion === runtimeVersion &&
        debugSignal?.sessionSummaryVersion === sessionSummaryVersion &&
        debugSignal?.resultCount > 0 &&
        debugSignal?.hasMatchedReason === true &&
        debugSignal?.hasEvidenceRefs === true &&
        debugSignal?.jumpActions?.includes("starfield") &&
        debugSignal?.jumpActions?.includes("river") &&
        debugSignal?.jumpActions?.includes("inspector") &&
        debugSignal?.directActiveMemoryWriteback === false &&
        debugSignal?.rawPrivateDataIncluded === false,
      "stage7_phase1_browser_debug_signal",
      "Stage 7.1 debug signal exposes result coverage, jump actions and safety flags",
      "Stage 7.1 debug signal is incomplete",
      debugSignal,
    );

    await fillSearch(page, "stage7-no-result-query-zzzz");
    await page.waitForSelector("[data-zero-result-recovery]", { timeout: 10_000 });
    const zeroRecovery = await page.evaluate(() => {
      const element = document.querySelector("[data-zero-result-recovery]");
      return {
        data: element?.getAttribute("data-zero-result-recovery") || null,
        text: element?.textContent || "",
      };
    });
    assertCondition(
      zeroRecovery.data === "search_2_0" &&
        ["broaden query", "remove filter", "related topic", "stale/archive", "later review hint"].every((text) =>
          zeroRecovery.text.includes(text),
        ),
      "stage7_phase1_browser_zero_recovery",
      "Zero-result state offers broaden, filter relaxation, related-topic, archive and later-review recovery actions",
      "Zero-result recovery is incomplete",
      zeroRecovery,
    );

    await fillSearch(page, "Codex");
    await page.waitForSelector("[data-search-result]", { timeout: 10_000 });
    const selectedResult = await firstResultSnapshot(page);
    await page.locator('[data-search-result] [data-search-jump="starfield"]').first().click({ timeout: 10_000 });
    await page.waitForSelector('[data-view="galaxy"]', { timeout: 10_000 });
    const starfieldState = await page.evaluate(() => ({
      activeView: document.querySelector("[data-view]")?.getAttribute("data-view") || null,
      selectedNode: document.querySelector(".galaxy-view")?.getAttribute("data-shared-focus-node") || "",
    }));
    assertCondition(
      starfieldState.activeView === "galaxy" && starfieldState.selectedNode === selectedResult.resultId,
      "stage7_phase1_browser_jump_starfield",
      "Search result jump_to_starfield switches to Starfield and preserves selected node",
      "Search result did not jump to Starfield with selected node",
      { selectedResult, starfieldState },
    );

    await openSearch(page);
    await fillSearch(page, "Codex");
    await page.waitForSelector("[data-search-result]", { timeout: 10_000 });
    const riverResult = await firstResultSnapshot(page);
    await page.locator('[data-search-result] [data-search-jump="river"]').first().click({ timeout: 10_000 });
    await page.waitForSelector('[data-view="timeline"]', { timeout: 10_000 });
    const riverState = await page.evaluate(() => ({
      activeView: document.querySelector("[data-view]")?.getAttribute("data-view") || null,
      selectedNode: document.querySelector(".timeline-map")?.getAttribute("data-shared-focus-node") || "",
    }));
    assertCondition(
      riverState.activeView === "timeline" && riverState.selectedNode === riverResult.resultId,
      "stage7_phase1_browser_jump_river",
      "Search result jump_to_river switches to Memory River and preserves selected node",
      "Search result did not jump to Memory River with selected node",
      { riverResult, riverState },
    );

    await openSearch(page);
    await fillSearch(page, "Codex");
    await page.waitForSelector("[data-search-result]", { timeout: 10_000 });
    const inspectorResult = await firstResultSnapshot(page);
    await page.locator('[data-search-result] [data-search-jump="inspector"]').first().click({ timeout: 10_000 });
    await page.waitForFunction(
      (nodeId) => document.querySelector(".inspector")?.getAttribute("data-shared-focus-node") === nodeId,
      inspectorResult.resultId,
      { timeout: 10_000 },
    );
    const inspectorState = await page.evaluate(() => ({
      activeView: document.querySelector("[data-view]")?.getAttribute("data-view") || null,
      selectedNode: document.querySelector(".inspector")?.getAttribute("data-shared-focus-node") || "",
    }));
    assertCondition(
      inspectorState.activeView === "search" && inspectorState.selectedNode === inspectorResult.resultId,
      "stage7_phase1_browser_open_inspector",
      "Search result open_inspector keeps Search 2.0 open and selects the Inspector node",
      "Search result did not open Inspector in Search 2.0",
      { inspectorResult, inspectorState },
    );

    const screenshotPath = path.join(outputDir, "search-2-0-stage7-phase1.png");
    await page.screenshot({ path: screenshotPath, fullPage: false });
    const screenshotBytes = fs.statSync(screenshotPath).size;
    assertCondition(
      screenshotBytes > 20_000,
      "stage7_phase1_browser_screenshot",
      `Browser Search 2.0 screenshot captured ${screenshotBytes} bytes`,
      "Browser Search 2.0 screenshot is unexpectedly small",
      { screenshotPath, screenshotBytes },
    );

    const actionableFailedResponses = failedResponses.filter((response) => {
      try {
        const pathname = new URL(response.url).pathname;
        return !["/__memory_atlas_runtime_state", "/__memory_atlas_heartbeat", "/__memory_atlas_release"].includes(pathname);
      } catch {
        return true;
      }
    });
    const actionableConsoleErrors = consoleMessages.filter((message) => {
      return !(message.startsWith("Failed to load resource:") && actionableFailedResponses.length === 0);
    });
    assertCondition(
      actionableConsoleErrors.length === 0 && actionableFailedResponses.length === 0,
      "stage7_phase1_browser_console",
      "Browser Search 2.0 test completed without actionable console errors or failed responses",
      "Browser Search 2.0 test produced actionable console errors or failed responses",
      { consoleMessages, failedResponses, actionableConsoleErrors, actionableFailedResponses },
    );

    await context.close();
    await browser.close();
    console.log(JSON.stringify({
      status: "PASS",
      validator: "validate_search_2_0_browser",
      url: targetUrl,
      output_dir: outputDir,
      checks,
    }, null, 2));
  } catch (error) {
    await context.close().catch(() => undefined);
    await browser.close().catch(() => undefined);
    console.error(JSON.stringify({
      status: "FAIL",
      validator: "validate_search_2_0_browser",
      url: targetUrl,
      output_dir: outputDir,
      error: error.message,
      details: error.details || null,
      checks,
      consoleMessages,
      failedResponses,
    }, null, 2));
    process.exit(1);
  }
}

main().catch((error) => {
  console.error(JSON.stringify({
    status: "FAIL",
    validator: "validate_search_2_0_browser",
    url: targetUrl,
    output_dir: outputDir,
    error: error.message,
    checks,
  }, null, 2));
  process.exit(1);
});
