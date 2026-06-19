#!/usr/bin/env node
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { chromium } = require("playwright");

const targetUrl = process.argv[2] || "http://127.0.0.1:4177";
const outputDir = process.env.MEMORY_ATLAS_VISUAL_AUDIT_DIR || fs.mkdtempSync(path.join(os.tmpdir(), "memory-atlas-galaxy-"));
const browserExecutable = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || findChromiumExecutable();

function findChromiumExecutable() {
  const candidates = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
  ];
  return candidates.find((candidate) => fs.existsSync(candidate));
}

function assertCondition(condition, message, details = {}) {
  if (!condition) {
    const error = new Error(message);
    error.details = details;
    throw error;
  }
}

async function readSignal(page) {
  return page.evaluate(() => window.__memoryAtlasGalaxySignal?.() ?? null);
}

async function readTargets(page) {
  return page.evaluate(() => window.__memoryAtlasGalaxyDebugTargets?.() ?? []);
}

async function verifyViewport(browser, viewport) {
  const page = await browser.newPage({
    deviceScaleFactor: 1,
    viewport: { width: viewport.width, height: viewport.height },
  });
  const consoleErrors = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => consoleErrors.push(error.message));

  await page.goto(targetUrl, { waitUntil: "domcontentloaded" });
  await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
  await page.getByRole("button", { name: /银河星云/ }).click({ timeout: 3000 }).catch(() => {});
  await page.waitForSelector(".galaxy-webgl-canvas", { timeout: 20000 });
  await page.waitForFunction(() => {
    const signal = window.__memoryAtlasGalaxySignal?.();
    return Boolean(signal && signal.lit > 100 && signal.alpha > 100 && signal.max > 42 && signal.width > 100 && signal.height > 100);
  }, null, { timeout: 20000 });

  const before = await readSignal(page);
  assertCondition(before, "Missing initial galaxy signal", { viewport });
  const beforePath = path.join(outputDir, `${viewport.name}-before.png`);
  await page.screenshot({ path: beforePath, fullPage: false });

  const targets = await readTargets(page);
  const target = targets.find((candidate) => Number.isFinite(candidate.x) && Number.isFinite(candidate.y) && candidate.linkedCount > 0);
  assertCondition(target, "No clickable linked galaxy target was exposed", { viewport, targets: targets.slice(0, 5) });

  await page.mouse.click(target.x, target.y);
  try {
    await page.waitForFunction(({ startingDistance, targetId }) => {
      const signal = window.__memoryAtlasGalaxySignal?.();
      return Boolean(
        signal
          && signal.focusNodeId === targetId
          && signal.highlightedNeighborCount > 0
          && signal.cameraDistance < startingDistance - 8,
      );
    }, { startingDistance: before.cameraDistance, targetId: target.id }, { timeout: 5000 });
  } catch {
    const afterTimeout = await readSignal(page);
    throw Object.assign(new Error("Galaxy click did not reach focus/pulse/camera threshold"), {
      details: { viewport, before, after: afterTimeout, target, targets: targets.slice(0, 8) },
    });
  }

  const after = await readSignal(page);
  const afterPath = path.join(outputDir, `${viewport.name}-after.png`);
  await page.screenshot({ path: afterPath, fullPage: false });
  assertCondition(after.focusNodeId === target.id, "Click did not select the intended galaxy node", { viewport, before, after, target });
  assertCondition(after.highlightedNeighborCount > 0, "Selected node did not expose neighbor pulse highlights", { viewport, before, after, target });
  assertCondition(after.cameraDistance < before.cameraDistance - 8, "Galaxy camera did not fly closer after node click", { viewport, before, after, target });
  assertCondition(after.lit > 100 && after.max > 42, "Galaxy canvas pixel signal became blank after click", { viewport, after });
  assertCondition(consoleErrors.length === 0, "Browser console/page errors occurred", { viewport, consoleErrors });

  await page.close();
  return {
    viewport: viewport.name,
    before,
    after,
    target,
    screenshots: [beforePath, afterPath],
  };
}

(async () => {
  const browser = await chromium.launch({
    executablePath: browserExecutable,
    headless: true,
  });
  try {
    const viewports = [
      { name: "desktop", width: 1440, height: 920 },
      { name: "mobile", width: 390, height: 844 },
    ];
    const results = [];
    for (const viewport of viewports) {
      results.push(await verifyViewport(browser, viewport));
    }
    console.log(JSON.stringify({ status: "PASS", outputDir, results }, null, 2));
  } catch (error) {
    console.error(JSON.stringify({ status: "FAIL", message: error.message, details: error.details || null, outputDir }, null, 2));
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
})();
