#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const outputDir = getArg("--output-dir") || fs.mkdtempSync(path.join(os.tmpdir(), "data-map-structure-browser-"));
const targetUrl = getArg("--url") || "http://127.0.0.1:5173/";
const browserExecutable = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || findChromiumExecutable();
const checks = [];

const structureModelVersion = "data_map_structure_model.v1_1_7_stage6_phase1";
const relationExplanationVersion = "data_map_relation_explanation.v1_1_7_stage6_phase1";

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
  await page.getByRole("button", { name: /数据导图/ }).click({ timeout: 10_000 });
  await page.waitForSelector(`[data-data-map-structure-model="${structureModelVersion}"]`, { timeout: 30_000 });
}

async function main() {
  fs.mkdirSync(outputDir, { recursive: true });
  const { chromium } = requirePlaywright();
  const browser = await chromium.launch({
    executablePath: browserExecutable,
    headless: true,
    args: ["--disable-dev-shm-usage"],
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
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

    const structure = await page.evaluate(() => {
      const root = document.querySelector("[data-data-map-structure-model]");
      const layers = Array.from(document.querySelectorAll("[data-data-map-layer]")).map((element) => ({
        id: element.getAttribute("data-data-map-layer"),
        label: element.textContent || "",
      }));
      return {
        structureModelVersion: root?.getAttribute("data-data-map-structure-model") || null,
        relationExplanationVersion: root?.getAttribute("data-data-map-relation-version") || null,
        layerIds: layers.map((layer) => layer.id),
        layerText: layers.map((layer) => layer.label).join(" "),
        relationCount: document.querySelectorAll("[data-data-map-relation-explanation]").length,
      };
    });
    assertCondition(
      structure.structureModelVersion === structureModelVersion &&
        structure.relationExplanationVersion === relationExplanationVersion &&
        structure.relationCount > 0,
      "stage6_phase1_browser_structure_model",
      "Production Data Guide exposes Stage 6.1 structure and relation explanation versions with clickable relations",
      "Data Guide structure model metadata is incomplete",
      structure,
    );

    const requiredLayers = ["source_layer", "profile_layer", "project_decision_layer", "action_opportunity_layer"];
    assertCondition(
      requiredLayers.every((layer) => structure.layerIds.includes(layer)) &&
        ["来源层", "画像层", "项目决策层", "行动机会层"].every((label) => structure.layerText.includes(label)),
      "stage6_phase1_browser_four_layers",
      "Data Guide renders source, profile, project decision and action opportunity layers",
      "Data Guide did not render the four required structure layers",
      structure,
    );

    const firstRelation = page.locator("[data-data-map-relation-explanation]").first();
    const relationBox = await firstRelation.boundingBox({ timeout: 10_000 });
    assertCondition(
      Boolean(relationBox),
      "stage6_phase1_browser_relation_box",
      "First Data Guide relation has a measurable browser layout box",
      "First Data Guide relation has no browser layout box",
    );
    const relationClickPoint = await firstRelation.evaluate((element) => {
      if (!(element instanceof SVGGeometryElement)) {
        throw new Error("relation hitbox is not an SVG geometry element");
      }
      const length = element.getTotalLength();
      const point = element.getPointAtLength(length / 2);
      const matrix = element.getScreenCTM();
      if (!matrix) throw new Error("relation hitbox has no screen transform");
      const screenPoint = new DOMPoint(point.x, point.y).matrixTransform(matrix);
      return { x: screenPoint.x, y: screenPoint.y, length };
    });
    await page.mouse.click(relationClickPoint.x, relationClickPoint.y);
    await page.waitForSelector(".data-map-relation-panel[data-selected-relation-id]", { timeout: 10_000 });
    const relationPanel = await page.evaluate(() => {
      const panel = document.querySelector(".data-map-relation-panel");
      const selectedRelation = document.querySelector("[data-data-map-relation-explanation][data-selected='true']");
      return {
        selectedRelationId: panel?.getAttribute("data-selected-relation-id") || null,
        source: panel?.getAttribute("data-relation-source") || null,
        strength: panel?.getAttribute("data-relation-strength") || null,
        evidence: panel?.getAttribute("data-relation-evidence") || null,
        time: panel?.getAttribute("data-relation-time") || null,
        selectedRelationMetadata: {
          source: selectedRelation?.getAttribute("data-relation-source") || null,
          strength: selectedRelation?.getAttribute("data-relation-strength") || null,
          evidence: selectedRelation?.getAttribute("data-relation-evidence") || null,
          time: selectedRelation?.getAttribute("data-relation-time") || null,
        },
        text: panel?.textContent || "",
      };
    });
    assertCondition(
      Boolean(relationPanel.selectedRelationId) &&
        Boolean(relationPanel.source) &&
        Boolean(relationPanel.strength) &&
        Boolean(relationPanel.evidence) &&
        Boolean(relationPanel.time) &&
        ["为什么连接", "来源", "强度", "证据", "时间"].every((text) => relationPanel.text.includes(text)),
      "stage6_phase1_browser_relation_click",
      "Clicking a Data Guide relation shows source, strength, evidence and time explanation",
      "Relation click did not expose the required explanation fields",
      { relationClickPoint, relationPanel },
    );

    const debugSignal = await page.evaluate(() => window.__memoryAtlasStage6Phase1?.() ?? null);
    assertCondition(
      debugSignal?.structureModelVersion === structureModelVersion &&
        debugSignal?.relationExplanationVersion === relationExplanationVersion &&
        requiredLayers.every((layer) => debugSignal?.layers?.includes(layer)) &&
        debugSignal?.proposalWrite === false &&
        debugSignal?.directActiveMemoryWriteback === false &&
        debugSignal?.rawPrivateDataIncluded === false,
      "stage6_phase1_browser_debug_signal",
      "Stage 6.1 debug signal exposes layer coverage and safe no-writeback flags",
      "Stage 6.1 debug signal is incomplete",
      debugSignal,
    );

    const screenshotPath = path.join(outputDir, "data-map-stage6-phase1.png");
    await page.screenshot({ path: screenshotPath, fullPage: false });
    const screenshotBytes = fs.statSync(screenshotPath).size;
    assertCondition(
      screenshotBytes > 20_000,
      "stage6_phase1_browser_screenshot",
      `Browser structure screenshot captured ${screenshotBytes} bytes`,
      "Browser structure screenshot is unexpectedly small",
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
      "stage6_phase1_browser_console",
      "Browser structure test completed without actionable console errors or failed responses",
      "Browser structure test produced actionable console errors or failed responses",
      { consoleMessages, failedResponses, actionableConsoleErrors, actionableFailedResponses },
    );

    await browser.close();
    console.log(
      JSON.stringify(
        {
          status: "PASS",
          validator: "validate_data_map_structure_browser",
          url: targetUrl,
          output_dir: outputDir,
          checks,
        },
        null,
        2,
      ),
    );
  } catch (error) {
    await browser.close();
    console.error(
      JSON.stringify(
        {
          status: "FAIL",
          validator: "validate_data_map_structure_browser",
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
