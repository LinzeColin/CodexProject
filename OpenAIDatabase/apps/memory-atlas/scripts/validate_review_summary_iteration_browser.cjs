#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const outputDir = getArg("--output-dir") || fs.mkdtempSync(path.join(os.tmpdir(), "review-summary-iteration-browser-"));
const targetUrl = getArg("--url") || "http://127.0.0.1:5173/";
const browserExecutable = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || findChromiumExecutable();
const checks = [];

const runtimeVersion = "review_summary_iteration_runtime.v1_1_7_stage7_phase2";
const reviewSchemaVersion = "memory_atlas_review_summary.v1_1_7_stage7_phase2";
const requiredPanelSelectors = [
  'data-review-panel="theme_change_panel"',
  'data-review-panel="proposal_decision_panel"',
  'data-review-panel="iteration_backlog"',
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
  await page.waitForSelector(`[data-review-summary-iteration-runtime="${runtimeVersion}"]`, { timeout: 30_000 });
}

async function runtimeSnapshot(page) {
  return page.evaluate(() => {
    const root = document.querySelector("[data-review-summary-iteration-runtime]");
    const panels = [...(root?.querySelectorAll("[data-review-panel]") || [])].map((node) =>
      node.getAttribute("data-review-panel"),
    );
    const questions = [...(root?.querySelectorAll("[data-review-question]") || [])].map((node) =>
      node.getAttribute("data-review-question"),
    );
    const output = root?.querySelector("[data-review-output-schema]");
    return {
      runtimeVersion: root?.getAttribute("data-review-summary-iteration-runtime") || null,
      reviewSchemaVersion: root?.getAttribute("data-review-schema-version") || null,
      periodSelector: Boolean(root?.querySelector("[data-review-period-selector]")),
      panels,
      questions,
      outputSchema: output?.getAttribute("data-review-output-schema") || null,
      proposalCandidate: output?.getAttribute("data-proposal-candidate") || null,
      evidenceRefs: output?.getAttribute("data-evidence-ref") || "",
      text: (root?.textContent || "").slice(0, 1200),
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
        root.reviewSchemaVersion === reviewSchemaVersion &&
        root.periodSelector === true,
      "stage7_phase2_browser_runtime_root",
      "Review / Summary / Iteration runtime root exposes versioned root and period selector",
      "Review / Summary / Iteration runtime root is incomplete",
      root,
    );

    const requiredPanels = [
      "theme_change_panel",
      "opportunity_panel",
      "low_value_loop_panel",
      "decision_change_panel",
      "next_action_panel",
      "proposal_decision_panel",
      "iteration_backlog",
    ];
    assertCondition(
      root.questions.length >= 8 &&
        requiredPanels.every((panel) => root.panels.includes(panel)) &&
        requiredPanelSelectors.every((selector) => selector.startsWith("data-review-panel=")) &&
        [
          "本期主导主题是什么",
          "哪些主题增强",
          "哪些主题衰退",
          "哪些新机会出现",
          "哪些低价值循环出现",
          "哪些决策变化",
          "下一步动作是什么",
          "是否需要生成 proposal",
        ].every((text) => root.text.includes(text)),
      "stage7_phase2_browser_eight_questions",
      "Runtime answers all eight review questions and exposes the required workflow panels",
      "Runtime is missing review questions or panels",
      root,
    );

    assertCondition(
      root.outputSchema === reviewSchemaVersion &&
        root.text.includes("dominant_topics") &&
        root.text.includes("strengthening_topics") &&
        root.text.includes("declining_topics") &&
        root.text.includes("new_opportunities") &&
        root.text.includes("low_value_loops") &&
        root.text.includes("decision_changes") &&
        root.text.includes("next_actions") &&
        root.text.includes("proposal_candidate") &&
        root.text.includes("iteration_backlog") &&
        root.evidenceRefs.length > 0,
      "stage7_phase2_browser_schema_output",
      "Runtime shows schema output, evidence refs, proposal decision and iteration backlog",
      "Runtime schema output is incomplete",
      root,
    );

    const debugSignal = await page.evaluate(() => window.__memoryAtlasStage7Phase2?.() ?? null);
    assertCondition(
      debugSignal?.runtimeVersion === runtimeVersion &&
        debugSignal?.reviewSchemaVersion === reviewSchemaVersion &&
        debugSignal?.questionCount >= 8 &&
        debugSignal?.panelIds?.includes("theme_change_panel") &&
        debugSignal?.panelIds?.includes("proposal_decision_panel") &&
        debugSignal?.panelIds?.includes("iteration_backlog") &&
        debugSignal?.iterationItemCount > 0 &&
        debugSignal?.hasEvidenceRefs === true &&
        debugSignal?.directActiveMemoryWriteback === false &&
        debugSignal?.rawPrivateDataIncluded === false,
      "stage7_phase2_browser_debug_signal",
      "Stage 7.2 debug signal exposes panel coverage, backlog, evidence and safety flags",
      "Stage 7.2 debug signal is incomplete",
      debugSignal,
    );

    const screenshotPath = path.join(outputDir, "review-summary-iteration-stage7-phase2.png");
    await page.screenshot({ path: screenshotPath, fullPage: false });
    const screenshotBytes = fs.statSync(screenshotPath).size;
    assertCondition(
      screenshotBytes > 20_000,
      "stage7_phase2_browser_screenshot",
      `Browser Review / Summary / Iteration screenshot captured ${screenshotBytes} bytes`,
      "Browser Review / Summary / Iteration screenshot is unexpectedly small",
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
      "stage7_phase2_browser_console",
      "Browser Review / Summary / Iteration test completed without actionable console errors or failed responses",
      "Browser Review / Summary / Iteration test produced actionable console errors or failed responses",
      { consoleMessages, failedResponses, actionableConsoleErrors, actionableFailedResponses },
    );

    await context.close();
    await browser.close();
    console.log(JSON.stringify({
      status: "PASS",
      validator: "validate_review_summary_iteration_browser",
      url: targetUrl,
      output_dir: outputDir,
      checks,
    }, null, 2));
  } catch (error) {
    await context.close().catch(() => undefined);
    await browser.close().catch(() => undefined);
    console.error(JSON.stringify({
      status: "FAIL",
      validator: "validate_review_summary_iteration_browser",
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
    validator: "validate_review_summary_iteration_browser",
    url: targetUrl,
    output_dir: outputDir,
    error: error.message,
    checks,
  }, null, 2));
  process.exit(1);
});
