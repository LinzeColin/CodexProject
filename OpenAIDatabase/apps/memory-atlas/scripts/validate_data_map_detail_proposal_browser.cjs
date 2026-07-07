#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const outputDir = getArg("--output-dir") || fs.mkdtempSync(path.join(os.tmpdir(), "data-map-detail-proposal-browser-"));
const targetUrl = getArg("--url") || "http://127.0.0.1:5173/";
const browserExecutable = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || findChromiumExecutable();
const checks = [];

const detailPanelVersion = "data_map_detail_panel.v1_1_7_stage6_phase2";
const proposalEntryVersion = "data_map_proposal_entry.v1_1_7_stage6_phase2";
const proposalDraftStoreKey = "memory-atlas.proposal-drafts.v1";

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

async function openDataMap(page) {
  await page.goto(targetUrl, { waitUntil: "networkidle", timeout: 30_000 });
  await page.evaluate((key) => window.localStorage.removeItem(key), proposalDraftStoreKey);
  await page.getByRole("button", { name: /数据导图/ }).click({ timeout: 10_000 });
  await page.waitForSelector(`[data-data-map-detail-panel="${detailPanelVersion}"]`, { timeout: 30_000 });
}

async function clickFirstMemoryNode(page) {
  const node = page.locator('[data-data-map-node-detail-entry][data-node-kind="memory"]').first();
  const box = await node.boundingBox({ timeout: 10_000 });
  assertCondition(Boolean(box), "stage6_phase2_browser_node_box", "First Data Guide memory node has a measurable browser layout box", "First Data Guide memory node has no browser layout box");
  await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
}

async function main() {
  fs.mkdirSync(outputDir, { recursive: true });
  const { chromium } = requirePlaywright();
  const browser = await chromium.launch({
    executablePath: browserExecutable,
    headless: true,
    args: ["--disable-dev-shm-usage"],
  });
  const context = await browser.newContext({ acceptDownloads: true, viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
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
    await openDataMap(page);
    await clickFirstMemoryNode(page);
    await page.waitForSelector(`.data-map-node-detail-panel[data-selected-node-id][data-data-map-detail-panel="${detailPanelVersion}"]`, {
      timeout: 10_000,
    });

    const detailPanel = await page.evaluate(() => {
      const panel = document.querySelector(".data-map-node-detail-panel");
      return {
        selectedNodeId: panel?.getAttribute("data-selected-node-id") || null,
        version: panel?.getAttribute("data-data-map-detail-panel") || null,
        asset: panel?.getAttribute("data-asset") || null,
        theme: panel?.getAttribute("data-theme") || null,
        action: panel?.getAttribute("data-suggested-action") || null,
        importance: panel?.getAttribute("data-importance") || null,
        priority: panel?.getAttribute("data-priority") || null,
        evidenceCount: panel?.getAttribute("data-evidence-count") || null,
        text: panel?.textContent || "",
      };
    });
    assertCondition(
      detailPanel.version === detailPanelVersion &&
        Boolean(detailPanel.selectedNodeId) &&
        ["资产", "主题", "建议动作", "重要性", "优先级"].every((text) => detailPanel.text.includes(text)) &&
        Boolean(detailPanel.asset) &&
        Boolean(detailPanel.theme) &&
        Boolean(detailPanel.action) &&
        Boolean(detailPanel.importance) &&
        Boolean(detailPanel.priority),
      "stage6_phase2_browser_detail_panel",
      "Clicking a Data Guide node shows the Stage 6.2 node detail panel",
      "Data Guide node detail panel did not expose required fields",
      detailPanel,
    );

    assertCondition(
      Number(detailPanel.evidenceCount || 0) >= 0 && detailPanel.text.includes("证据"),
      "stage6_phase2_browser_detail_fields",
      "Detail panel shows asset, theme, suggested action, importance, priority and evidence summary",
      "Detail panel field coverage is incomplete",
      detailPanel,
    );

    const proposalEntry = await page.evaluate(() => {
      const entry = document.querySelector(".data-map-proposal-entry");
      const editor = entry?.querySelector(".proposal-editor");
      return {
        version: entry?.getAttribute("data-data-map-proposal-entry") || null,
        proposalOnly: entry?.getAttribute("data-proposal-only") || null,
        activeMemoryMutation: entry?.getAttribute("data-active-memory-mutation") || null,
        directWriteback: entry?.getAttribute("data-direct-active-memory-writeback") || null,
        sourceSurface: entry?.getAttribute("data-source-surface") || null,
        editorProposalOnly: editor?.getAttribute("data-proposal-only") || null,
        text: entry?.textContent || "",
      };
    });
    assertCondition(
      proposalEntry.version === proposalEntryVersion &&
        proposalEntry.proposalOnly === "true" &&
        proposalEntry.activeMemoryMutation === "false" &&
        proposalEntry.directWriteback === "false" &&
        proposalEntry.sourceSurface === "data_guide_detail_panel" &&
        proposalEntry.editorProposalOnly === "true" &&
        ["importance", "priority", "导出 proposal JSON"].every((text) => proposalEntry.text.includes(text)),
      "stage6_phase2_browser_proposal_entry",
      "Data Guide detail panel embeds proposal-only importance and priority controls",
      "Data Guide proposal entry is incomplete or unsafe",
      proposalEntry,
    );

    const importanceSlider = page.getByLabel("调整 importance");
    const currentImportanceValue = await importanceSlider.inputValue();
    await importanceSlider.fill(currentImportanceValue === "0" ? "2" : "0");
    await page.getByLabel("proposal note").fill("Stage 6.2 browser proposal-only export check.");
    await page.waitForFunction(() => {
      const preview = document.querySelector(".proposal-diff-preview");
      return Boolean(preview?.textContent?.includes("importance"));
    }, null, { timeout: 5_000 });
    const downloadPromise = page.waitForEvent("download", { timeout: 10_000 });
    await page.getByRole("button", { name: /导出 proposal JSON/ }).click({ timeout: 10_000 });
    const download = await downloadPromise;
    const downloadedPath = await download.path();
    const exportPayload = JSON.parse(fs.readFileSync(downloadedPath, "utf8"));
    const storeSnapshot = await page.evaluate((key) => {
      const raw = window.localStorage.getItem(key);
      return raw ? JSON.parse(raw) : null;
    }, proposalDraftStoreKey);
    assertCondition(
      exportPayload.schema_version === "memory_atlas_proposal_export.v1" &&
        exportPayload.source_surface === "data_guide_detail_panel" &&
        exportPayload.safety?.proposal_only === true &&
        exportPayload.safety?.direct_frontend_mutation_of_active_memory === false &&
        exportPayload.safety?.requires_agent_or_human_apply === true &&
        exportPayload.changes?.some((change) => change.field === "importance") &&
        exportPayload.changes?.some((change) => change.field === "note") &&
        storeSnapshot === null,
      "stage6_phase2_browser_proposal_export",
      "Data Guide proposal entry exports a proposal-only JSON payload without writing local draft store or active memory",
      "Proposal export did not preserve proposal-only safety",
      {
        filename: download.suggestedFilename(),
        target: exportPayload.target_ref,
        safety: exportPayload.safety,
        changeFields: exportPayload.changes?.map((change) => change.field),
        localDraftStoreAfterExport: storeSnapshot,
      },
    );

    const debugSignal = await page.evaluate(() => window.__memoryAtlasStage6Phase2?.() ?? null);
    assertCondition(
      debugSignal?.detailPanelVersion === detailPanelVersion &&
        debugSignal?.proposalEntryVersion === proposalEntryVersion &&
        debugSignal?.selectedNodeId === detailPanel.selectedNodeId &&
        debugSignal?.detailFields?.includes("asset") &&
        debugSignal?.detailFields?.includes("theme") &&
        debugSignal?.detailFields?.includes("suggested_action") &&
        debugSignal?.detailFields?.includes("importance") &&
        debugSignal?.detailFields?.includes("priority") &&
        debugSignal?.proposalOnly === true &&
        debugSignal?.directActiveMemoryWriteback === false &&
        debugSignal?.rawPrivateDataIncluded === false,
      "stage6_phase2_browser_debug_signal",
      "Stage 6.2 debug signal exposes selected detail fields and proposal-only safety flags",
      "Stage 6.2 debug signal is incomplete",
      debugSignal,
    );

    const screenshotPath = path.join(outputDir, "data-map-stage6-phase2.png");
    await page.screenshot({ path: screenshotPath, fullPage: false });
    const screenshotBytes = fs.statSync(screenshotPath).size;
    assertCondition(
      screenshotBytes > 20_000,
      "stage6_phase2_browser_screenshot",
      `Browser detail/proposal screenshot captured ${screenshotBytes} bytes`,
      "Browser detail/proposal screenshot is unexpectedly small",
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
      "stage6_phase2_browser_console",
      "Browser detail/proposal test completed without actionable console errors or failed responses",
      "Browser detail/proposal test produced actionable console errors or failed responses",
      { consoleMessages, failedResponses, actionableConsoleErrors, actionableFailedResponses },
    );

    await context.close();
    await browser.close();
    console.log(
      JSON.stringify(
        {
          status: "PASS",
          validator: "validate_data_map_detail_proposal_browser",
          url: targetUrl,
          output_dir: outputDir,
          checks,
        },
        null,
        2,
      ),
    );
  } catch (error) {
    await context.close();
    await browser.close();
    console.error(
      JSON.stringify(
        {
          status: "FAIL",
          validator: "validate_data_map_detail_proposal_browser",
          url: targetUrl,
          output_dir: outputDir,
          error: error.message,
          details: error.details || null,
          checks,
        },
        null,
        2,
      ),
    );
    process.exit(1);
  }
}

main();
