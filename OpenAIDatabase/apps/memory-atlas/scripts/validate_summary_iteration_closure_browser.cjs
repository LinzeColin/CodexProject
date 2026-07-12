#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const outputDir = getArg("--output-dir") || fs.mkdtempSync(path.join(os.tmpdir(), "summary-iteration-closure-browser-"));
const targetUrl = getArg("--url") || "http://127.0.0.1:5173/";
const browserExecutable = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || findChromiumExecutable();
const checks = [];

const runtimeVersion = "summary_iteration_closure_runtime.v1_1_7_stage8_phase1";
const closureSchemaVersion = "memory_atlas_summary_closure.v1_1_7_stage8_phase1";
const reviewSchemaVersion = "memory_atlas_review_summary.v1_1_7_stage7_phase2";
const requiredPanelSelectors = [
  'data-summary-closure-panel="change_comparison"',
  'data-summary-closure-panel="stale_conflict_signals"',
  'data-summary-closure-panel="proposal_candidates"',
];

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

async function openSummary(page) {
  await page.goto(targetUrl, { waitUntil: "networkidle", timeout: 30_000 });
  await page.locator('[data-nav-view="summary"]').click({ timeout: 10_000 });
  await page.waitForSelector(`[data-summary-iteration-closure-runtime="${runtimeVersion}"]`, { timeout: 30_000 });
}

async function runtimeSnapshot(page) {
  return page.evaluate(() => {
    const root = document.querySelector("[data-summary-iteration-closure-runtime]");
    const panels = [...(root?.querySelectorAll("[data-summary-closure-panel]") || [])].map((node) =>
      node.getAttribute("data-summary-closure-panel"),
    );
    const outputText = root?.textContent || "";
    return {
      runtimeVersion: root?.getAttribute("data-summary-iteration-closure-runtime") || null,
      closureSchemaVersion: root?.getAttribute("data-summary-closure-schema-version") || null,
      sourceReviewSchemaVersion: root?.getAttribute("data-source-review-schema-version") || null,
      panels,
      proposalCount: root?.querySelectorAll('[data-summary-closure-panel="proposal_candidates"] section').length || 0,
      signalCount: root?.querySelectorAll("[data-summary-signal-type]").length || 0,
      hasRollbackHint: /rollback|回滚|丢弃 candidate/.test(outputText),
      hasProposalHint: /proposal/i.test(outputText),
      hasRequiresConflictCheck: outputText.includes("requires_conflict_check=true"),
      hasRequiresAgentOrHumanApply: outputText.includes("requires_agent_or_human_apply=true"),
      hasProposalOnly: outputText.includes("仅生成提案：是"),
      text: outputText.slice(0, 1600),
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
    await openSummary(page);
    const root = await runtimeSnapshot(page);
    assertCondition(
      root.runtimeVersion === runtimeVersion &&
        root.closureSchemaVersion === closureSchemaVersion &&
        root.sourceReviewSchemaVersion === reviewSchemaVersion,
      "stage8_phase1_browser_runtime_root",
      "Summary and iteration closure runtime root exposes versioned runtime, closure schema and source review schema",
      "Summary and iteration closure runtime root is incomplete",
      root,
    );

    assertCondition(
      root.panels.includes("change_comparison") &&
        requiredPanelSelectors.includes('data-summary-closure-panel="change_comparison"') &&
        root.text.includes("change_comparison") &&
        root.text.includes("当前") &&
        root.text.includes("上期") &&
        root.text.includes("evidence_refs"),
      "stage8_phase1_browser_change_comparison",
      "Runtime shows change_comparison with current/previous Chinese counts and evidence refs",
      "Runtime change_comparison panel is incomplete",
      root,
    );

    assertCondition(
      root.panels.includes("stale_conflict_signals") &&
        requiredPanelSelectors.includes('data-summary-closure-panel="stale_conflict_signals"') &&
        root.signalCount >= 1 &&
        root.text.includes("stale_conflict_signals") &&
        root.hasRollbackHint === true &&
        root.hasProposalHint === true,
      "stage8_phase1_browser_stale_conflict_signals",
      "Runtime shows stale/conflict signals with proposal hints and rollback hints",
      "Runtime stale/conflict signals are incomplete",
      root,
    );

    assertCondition(
      root.panels.includes("proposal_candidates") &&
        requiredPanelSelectors.includes('data-summary-closure-panel="proposal_candidates"') &&
        root.proposalCount >= 1 &&
        root.text.includes("proposal_candidates") &&
        root.hasRequiresConflictCheck === true &&
        root.hasRequiresAgentOrHumanApply === true &&
        root.hasProposalOnly === true,
      "stage8_phase1_browser_proposal_candidates",
      "Runtime shows proposal candidates with conflict check, human/agent apply gate and proposal-only safety",
      "Runtime proposal candidates are incomplete",
      root,
    );

    const debugSignal = await page.evaluate(() => window.__memoryAtlasStage8Phase1?.() ?? null);
    assertCondition(
      debugSignal?.runtimeVersion === runtimeVersion &&
        debugSignal?.closureSchemaVersion === closureSchemaVersion &&
        debugSignal?.sourceReviewSchemaVersion === reviewSchemaVersion &&
        debugSignal?.panelIds?.includes("change_comparison") &&
        debugSignal?.panelIds?.includes("stale_conflict_signals") &&
        debugSignal?.panelIds?.includes("proposal_candidates") &&
        debugSignal?.changeComparisonCount >= 1 &&
        debugSignal?.staleConflictSignalCount >= 1 &&
        debugSignal?.proposalCandidateCount >= 1 &&
        debugSignal?.proposalOnly === true &&
        debugSignal?.directActiveMemoryWriteback === false &&
        debugSignal?.rawPrivateDataIncluded === false &&
        debugSignal?.proposalWrite === false,
      "stage8_phase1_browser_debug_signal",
      "Stage 8.1 debug signal exposes closure coverage and safety flags",
      "Stage 8.1 debug signal is incomplete",
      debugSignal,
    );

    const screenshotPath = path.join(outputDir, "summary-iteration-closure-stage8-phase1.png");
    await page.screenshot({ path: screenshotPath, fullPage: false });
    const screenshotBytes = fs.statSync(screenshotPath).size;
    assertCondition(
      screenshotBytes > 20_000,
      "stage8_phase1_browser_screenshot",
      `Browser Summary and Iteration Closure screenshot captured ${screenshotBytes} bytes`,
      "Browser Summary and Iteration Closure screenshot is unexpectedly small",
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
      "stage8_phase1_browser_console",
      "Browser Summary and Iteration Closure test completed without actionable console errors or failed responses",
      "Browser Summary and Iteration Closure test produced actionable console errors or failed responses",
      { consoleMessages, failedResponses, actionableConsoleErrors, actionableFailedResponses },
    );
  } finally {
    await browser.close();
  }

  console.log(JSON.stringify({
    status: "PASS",
    validator: "validate_summary_iteration_closure_browser",
    runtime_version: runtimeVersion,
    closure_schema_version: closureSchemaVersion,
    output_dir: outputDir,
    checks,
  }, null, 2));
}

main().catch((error) => {
  console.error(JSON.stringify({
    status: "FAIL",
    validator: "validate_summary_iteration_closure_browser",
    runtime_version: runtimeVersion,
    closure_schema_version: closureSchemaVersion,
    error: error.message,
    details: error.details || null,
    checks,
  }, null, 2));
  process.exit(1);
});
