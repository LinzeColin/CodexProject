#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const http = require("node:http");
const os = require("node:os");
const path = require("node:path");
const { spawn } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const port = Number(process.env.MEMORY_ATLAS_V1_2_HOME_PORT || 4178);
const targetUrl = `http://127.0.0.1:${port}`;
const outputDir = process.env.MEMORY_ATLAS_V1_2_HOME_AUDIT_DIR
  || fs.mkdtempSync(path.join(os.tmpdir(), "memory-atlas-v1-2-home-"));
const browserExecutable = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || findChromiumExecutable();
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
  const pnpmRoot = path.join(
    os.homedir(),
    ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm",
  );
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
    request.setTimeout(timeoutMs, () => request.destroy(new Error(`timeout waiting for ${url}`)));
    request.on("error", reject);
  });
}

async function waitForHttp(url, server, timeoutMs = 20000) {
  const started = Date.now();
  let lastError = null;
  while (Date.now() - started < timeoutMs) {
    if (server.exitCode !== null) {
      throw new Error(`Vite preview exited before readiness with code ${server.exitCode}`);
    }
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
  const server = spawn(
    process.execPath,
    [viteCli, "preview", "--host", "127.0.0.1", "--port", String(port), "--strictPort"],
    { cwd: appRoot, env: { ...process.env }, stdio: ["ignore", "pipe", "pipe"] },
  );
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

function roundedRect(rect) {
  if (!rect) return null;
  return Object.fromEntries(
    ["x", "y", "top", "right", "bottom", "left", "width", "height"]
      .map((key) => [key, Math.round(rect[key] * 10) / 10]),
  );
}

function assertNoPairwiseOverlap(layout) {
  const entries = Object.entries(layout.sections).filter(([, rect]) => rect);
  const overlaps = [];
  for (let leftIndex = 0; leftIndex < entries.length; leftIndex += 1) {
    for (let rightIndex = leftIndex + 1; rightIndex < entries.length; rightIndex += 1) {
      const [leftName, leftRect] = entries[leftIndex];
      const [rightName, rightRect] = entries[rightIndex];
      const overlapWidth = Math.min(leftRect.right, rightRect.right) - Math.max(leftRect.left, rightRect.left);
      const overlapHeight = Math.min(leftRect.bottom, rightRect.bottom) - Math.max(leftRect.top, rightRect.top);
      if (overlapWidth > 1 && overlapHeight > 1) {
        overlaps.push({
          first: leftName,
          second: rightName,
          overlapWidth: Math.round(overlapWidth * 10) / 10,
          overlapHeight: Math.round(overlapHeight * 10) / 10,
        });
      }
    }
  }
  assertCondition(overlaps.length === 0, "Workspace sections overlap", { overlaps, sections: layout.sections });
}

function assertNoHorizontalOverflow(layout) {
  const overflow = layout.document.scrollWidth - layout.document.clientWidth;
  const escapedSections = Object.entries(layout.sections)
    .filter(([, rect]) => rect)
    .filter(([, rect]) => rect.left < layout.workspace.left - 1 || rect.right > layout.workspace.right + 1)
    .map(([name, rect]) => ({ name, rect }));
  assertCondition(overflow <= 1 && escapedSections.length === 0, "Home layout has horizontal overflow", {
    document: layout.document,
    escapedSections,
    overflow,
  });
}

function assertViewportContainment(layout) {
  const escapedSections = Object.entries(layout.sections)
    .filter(([, rect]) => rect)
    .filter(([, rect]) => rect.top < layout.workspace.top - 1 || rect.bottom > layout.workspace.bottom + 1)
    .map(([name, rect]) => ({ name, rect }));
  const workspaceEscaped = layout.workspace.top < -1
    || layout.workspace.bottom > layout.document.clientHeight + 1;
  assertCondition(!workspaceEscaped && escapedSections.length === 0, "Home layout escapes the visible viewport", {
    document: layout.document,
    escapedSections,
    workspace: layout.workspace,
  });
}

async function assertPaletteContentReachable(page, viewport) {
  const result = await page.evaluate(() => {
    const palette = document.querySelector(".command-palette");
    const heading = palette?.querySelector(".command-palette-heading");
    const detail = palette?.querySelector(".command-palette-detail");
    const lastSafetyItem = palette?.querySelector(".command-palette-safety span:last-child");
    if (!palette || !heading || !detail || !lastSafetyItem) return null;

    const intersects = (container, element) => {
      const containerRect = container.getBoundingClientRect();
      const elementRect = element.getBoundingClientRect();
      return elementRect.bottom > containerRect.top + 1 && elementRect.top < containerRect.bottom - 1;
    };

    palette.scrollTop = 0;
    const topVisible = intersects(palette, heading);
    const maxScroll = palette.scrollHeight - palette.clientHeight;
    palette.scrollTop = maxScroll;
    const movedToBottom = palette.scrollTop;
    const bottomVisible = intersects(palette, lastSafetyItem);
    const paletteRect = palette.getBoundingClientRect();
    const detailRect = detail.getBoundingClientRect();
    const detailContentTop = detailRect.top - paletteRect.top + palette.scrollTop;
    palette.scrollTop = Math.max(
      0,
      Math.min(maxScroll, detailContentTop - (palette.clientHeight - Math.min(detail.clientHeight, palette.clientHeight)) / 2),
    );
    const detailVisible = intersects(palette, detail);
    const style = getComputedStyle(palette);

    return {
      bottomVisible,
      clientHeight: palette.clientHeight,
      detailVisible,
      maxScroll,
      movedToBottom,
      overflowY: style.overflowY,
      scrollHeight: palette.scrollHeight,
      topVisible,
    };
  });

  const minimumHeight = viewport.width <= 720 ? 128 : 156;
  assertCondition(Boolean(result), "Command palette content is missing");
  assertCondition(["auto", "scroll"].includes(result.overflowY), "Command palette is not a scroll container", result);
  assertCondition(result.clientHeight >= minimumHeight, "Command palette viewport is too short to use", {
    ...result,
    minimumHeight,
  });
  assertCondition(result.maxScroll > 0 && result.movedToBottom >= result.maxScroll - 2, "Command palette cannot reach its bottom content", result);
  assertCondition(result.topVisible && result.detailVisible && result.bottomVisible, "Command palette critical content is clipped", result);
  return result;
}

async function assertCriticalContentReachable(page, viewport) {
  const result = await page.evaluate(() => {
    const contentGrid = document.querySelector(".content-grid");
    const viewSurface = document.querySelector(".view-surface");
    const home = document.querySelector(".home-overview-view");
    const firstSection = home?.querySelector(".surface-heading");
    const lastSection = home?.querySelector(".home-topic-strip");
    if (!contentGrid || !viewSurface || !home || !firstSection || !lastSection) return null;

    const intersects = (container, element) => {
      const containerRect = container.getBoundingClientRect();
      const elementRect = element.getBoundingClientRect();
      return elementRect.bottom > containerRect.top + 1 && elementRect.top < containerRect.bottom - 1;
    };

    home.scrollTop = 0;
    const topVisible = intersects(home, firstSection);
    const maxScroll = home.scrollHeight - home.clientHeight;
    home.scrollTop = maxScroll;
    const movedToBottom = home.scrollTop;
    const homeRect = home.getBoundingClientRect();
    const lastRect = lastSection.getBoundingClientRect();
    const lastContentTop = lastRect.top - homeRect.top + home.scrollTop;
    home.scrollTop = Math.max(
      0,
      Math.min(maxScroll, lastContentTop - (home.clientHeight - Math.min(lastSection.clientHeight, home.clientHeight)) / 2),
    );
    const movedToLastSection = home.scrollTop;
    const bottomVisible = intersects(home, lastSection);
    const style = getComputedStyle(home);
    const contentGridRect = contentGrid.getBoundingClientRect();
    const viewSurfaceRect = viewSurface.getBoundingClientRect();
    const finalHomeRect = home.getBoundingClientRect();

    return {
      bottomVisible,
      clientHeight: home.clientHeight,
      contentGridHeight: contentGridRect.height,
      homeContainedBySurface:
        finalHomeRect.top >= viewSurfaceRect.top - 1
        && finalHomeRect.bottom <= viewSurfaceRect.bottom + 1,
      maxScroll,
      movedToBottom,
      movedToLastSection,
      overflowY: style.overflowY,
      scrollHeight: home.scrollHeight,
      surfaceContainedByGrid:
        viewSurfaceRect.top >= contentGridRect.top - 1
        && viewSurfaceRect.bottom <= contentGridRect.bottom + 1,
      surfaceHeight: viewSurfaceRect.height,
      topVisible,
    };
  });

  const minimumHeight = viewport.width <= 720 ? 120 : 160;
  assertCondition(Boolean(result), "Home critical content is missing");
  assertCondition(result.contentGridHeight >= minimumHeight, "Home content viewport is too short to use", {
    ...result,
    minimumHeight,
  });
  assertCondition(
    result.surfaceContainedByGrid && result.homeContainedBySurface,
    "Home overview escapes its visible content surface",
    result,
  );
  assertCondition(["auto", "scroll"].includes(result.overflowY), "Home overview is not a scroll container", result);
  assertCondition(result.maxScroll > 0 && result.movedToBottom >= result.maxScroll - 2, "Home overview cannot reach its final section", result);
  assertCondition(result.topVisible && result.bottomVisible, "Home overview critical sections are clipped", result);
  return result;
}

async function assertNestedHomeContentFits(page) {
  const result = await page.evaluate(() => {
    const home = document.querySelector(".home-overview-view");
    if (!home) return null;

    const nestedContainerSelector = [
      ".arrival-briefing-grid",
      ".home-structure-rail",
      ".home-primary-band",
      ".home-status-grid",
      ".home-behavior-count-row",
      ".home-behavior-card-grid",
      ".home-preview-grid",
      ".home-action-list",
      ".home-operation-chip-grid",
      ".home-section-summary-row",
      ".home-inspector-link-list",
      ".home-tier-asset-grid",
      ".home-topic-detail-grid",
      ".home-topic-strip",
    ].join(",");
    const targets = new Set([
      ...Array.from(home.children),
      ...Array.from(home.querySelectorAll(nestedContainerSelector)),
    ]);
    const homeRect = home.getBoundingClientRect();
    const issues = [];
    let inspectedChildren = 0;

    const rendered = (element) => {
      const style = getComputedStyle(element);
      const rect = element.getBoundingClientRect();
      return style.display !== "none"
        && style.visibility !== "hidden"
        && rect.width > 1
        && rect.height > 1;
    };
    const label = (element) => {
      const className = typeof element.className === "string" ? element.className.trim() : "";
      return className || element.tagName.toLowerCase();
    };
    const escaped = (inner, outer) => inner.left < outer.left - 1 || inner.right > outer.right + 1;

    for (const target of targets) {
      if (!rendered(target)) continue;
      const targetRect = target.getBoundingClientRect();
      const ownOverflow = target.scrollWidth - target.clientWidth;
      if (escaped(targetRect, homeRect)) {
        issues.push({ kind: "target_escapes_home", target: label(target), targetRect, homeRect });
      }
      if (ownOverflow > 1) {
        issues.push({
          kind: "target_scroll_width_overflow",
          target: label(target),
          clientWidth: target.clientWidth,
          scrollWidth: target.scrollWidth,
          overflow: ownOverflow,
        });
      }

      if (!target.matches(nestedContainerSelector)) continue;
      for (const child of target.children) {
        if (!rendered(child)) continue;
        inspectedChildren += 1;
        const childRect = child.getBoundingClientRect();
        if (escaped(childRect, targetRect)) {
          issues.push({
            kind: "child_escapes_container",
            container: label(target),
            child: label(child),
            childRect,
            containerRect: targetRect,
          });
        }
      }
    }

    return {
      inspectedChildren,
      inspectedTargets: Array.from(targets).filter(rendered).length,
      issueCount: issues.length,
      issues: issues.slice(0, 30),
    };
  });

  assertCondition(Boolean(result), "Home nested content is missing");
  assertCondition(result.inspectedTargets >= 12 && result.inspectedChildren >= 12, "Home nested overflow coverage is unexpectedly sparse", result);
  assertCondition(result.issueCount === 0, "Home nested content has horizontal clipping or overflow", result);
  return result;
}

async function assertBehaviorSummariesReachable(page) {
  const result = await page.evaluate(() => {
    const home = document.querySelector(".home-overview-view");
    const panel = home?.querySelector(".home-behavior-intelligence-panel");
    const cards = panel ? Array.from(panel.querySelectorAll(".home-behavior-card")) : [];
    if (!home || !panel) return null;

    const maxScroll = home.scrollHeight - home.clientHeight;
    const summaryResults = [];
    for (const summary of panel.querySelectorAll(".home-behavior-item p")) {
      const homeRect = home.getBoundingClientRect();
      const summaryRect = summary.getBoundingClientRect();
      const contentTop = summaryRect.top - homeRect.top + home.scrollTop;
      home.scrollTop = Math.max(
        0,
        Math.min(maxScroll, contentTop - (home.clientHeight - Math.min(summary.clientHeight, home.clientHeight)) / 2),
      );
      const visibleHomeRect = home.getBoundingClientRect();
      const visibleSummaryRect = summary.getBoundingClientRect();
      const text = summary.textContent?.trim() || "";
      const style = getComputedStyle(summary);
      summaryResults.push({
        chinese: /[\u3400-\u9fff]/.test(text),
        reachable:
          style.display !== "none"
          && style.visibility !== "hidden"
          && visibleSummaryRect.height > 1
          && visibleSummaryRect.bottom > visibleHomeRect.top + 1
          && visibleSummaryRect.top < visibleHomeRect.bottom - 1,
        text: text.slice(0, 120),
      });
    }

    return {
      cardCount: cards.length,
      cardSummaryCounts: cards.map((card) => card.querySelectorAll(".home-behavior-item p").length),
      chineseSummaryCount: summaryResults.filter((item) => item.chinese).length,
      reachableSummaryCount: summaryResults.filter((item) => item.reachable).length,
      summaries: summaryResults,
      summaryCount: summaryResults.length,
    };
  });

  assertCondition(Boolean(result), "S06 behavior intelligence panel is missing");
  assertCondition(result.cardCount === 3 && result.cardSummaryCounts.every((count) => count === 3), "S06 behavior categories are incomplete", result);
  assertCondition(result.summaryCount === 9, "S06 behavior summaries are unexpectedly sparse", result);
  assertCondition(result.chineseSummaryCount === result.summaryCount, "S06 behavior summaries are not Chinese-readable", result);
  assertCondition(result.reachableSummaryCount === result.summaryCount, "S06 behavior summaries are not scroll-reachable", result);
  return result;
}

function isIgnoredRuntimeProbe(response) {
  try {
    const pathname = new URL(response.url).pathname;
    return response.status === 404 && ["/__memory_atlas_heartbeat", "/__memory_atlas_release"].includes(pathname);
  } catch {
    return false;
  }
}

async function captureLayout(page) {
  return page.evaluate(() => {
    const rect = (selector) => {
      const element = document.querySelector(selector);
      if (!element) return null;
      const box = element.getBoundingClientRect();
      return Object.fromEntries(
        ["x", "y", "top", "right", "bottom", "left", "width", "height"]
          .map((key) => [key, box[key]]),
      );
    };
    const documentElement = document.documentElement;
    return {
      document: {
        clientHeight: documentElement.clientHeight,
        clientWidth: documentElement.clientWidth,
        scrollHeight: documentElement.scrollHeight,
        scrollWidth: documentElement.scrollWidth,
      },
      sections: {
        topbar: rect(".topbar"),
        controls: rect(".controls"),
        interactionLens: rect(".interaction-lens"),
        commandPalette: rect(".command-palette"),
        contentGrid: rect(".content-grid"),
      },
      workspace: rect(".workspace"),
    };
  });
}

async function validateViewport(browser, viewport) {
  const page = await browser.newPage({
    viewport: { width: viewport.width, height: viewport.height },
    deviceScaleFactor: 1,
  });
  const consoleErrors = [];
  const failedResponses = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => consoleErrors.push(error.message));
  page.on("response", (response) => {
    if (response.status() >= 400) failedResponses.push({ status: response.status(), url: response.url() });
  });

  try {
    await page.goto(targetUrl, { waitUntil: "domcontentloaded", timeout: 20000 });
    await page.waitForSelector("[data-s12-p1-command-palette]", { timeout: 15000 });
    await page.waitForSelector(".home-overview-view", { timeout: 15000 });
    await page.waitForTimeout(250);

    const rawLayout = await captureLayout(page);
    const layout = {
      document: rawLayout.document,
      sections: Object.fromEntries(Object.entries(rawLayout.sections).map(([key, value]) => [key, roundedRect(value)])),
      workspace: roundedRect(rawLayout.workspace),
    };
    const screenshotPath = path.join(outputDir, `home-${viewport.name}-${viewport.width}x${viewport.height}.png`);
    await page.screenshot({ path: screenshotPath, fullPage: false });
    const screenshotBytes = fs.statSync(screenshotPath).size;
    assertCondition(screenshotBytes > 15_000, "Home screenshot is unexpectedly small", {
      screenshotBytes,
      screenshotPath,
    });

    assertNoPairwiseOverlap(layout);
    assertNoHorizontalOverflow(layout);
    assertViewportContainment(layout);
    const palette = await assertPaletteContentReachable(page, viewport);
    const criticalContent = await assertCriticalContentReachable(page, viewport);
    const nestedHomeContent = await assertNestedHomeContentFits(page);
    const behaviorSummaries = await assertBehaviorSummariesReachable(page);
    const actionableFailedResponses = failedResponses.filter((response) => !isIgnoredRuntimeProbe(response));
    const actionableConsoleErrors = consoleErrors.filter((message) => {
      return !(message.startsWith("Failed to load resource:") && actionableFailedResponses.length === 0);
    });
    assertCondition(
      actionableConsoleErrors.length === 0 && actionableFailedResponses.length === 0,
      "Browser console/page errors occurred",
      { actionableConsoleErrors, actionableFailedResponses, consoleErrors, failedResponses },
    );

    return {
      status: "PASS",
      viewport,
      layout,
      palette,
      criticalContent,
      nestedHomeContent,
      behaviorSummaries,
      screenshot: { path: screenshotPath, bytes: screenshotBytes },
      consoleErrors,
      failedResponses,
      actionableConsoleErrors,
      actionableFailedResponses,
    };
  } catch (error) {
    const screenshotPath = path.join(outputDir, `home-${viewport.name}-${viewport.width}x${viewport.height}-failure.png`);
    await page.screenshot({ path: screenshotPath, fullPage: false }).catch(() => undefined);
    return {
      status: "FAIL",
      viewport,
      message: error.message,
      details: error.details || null,
      screenshot: fs.existsSync(screenshotPath)
        ? { path: screenshotPath, bytes: fs.statSync(screenshotPath).size }
        : null,
      consoleErrors,
      failedResponses,
    };
  } finally {
    await page.close();
  }
}

async function runBrowserValidation() {
  const { chromium } = requirePlaywright();
  assertCondition(Boolean(browserExecutable), "No Chromium-compatible browser executable found");
  const browser = await chromium.launch({ executablePath: browserExecutable, headless: true });
  try {
    const results = [];
    for (const viewport of viewports) {
      results.push(await validateViewport(browser, viewport));
    }
    const failures = results.filter((result) => result.status !== "PASS");
    assertCondition(failures.length === 0, "One or more v1.2 home viewport contracts failed", { failures });
    return results;
  } finally {
    await browser.close();
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
    preview = startPreviewServer();
    await waitForHttp(targetUrl, preview.server);
    const results = await runBrowserValidation();
    await stopPreviewServer(preview.server);
    await assertPortClosed();
    const payload = {
      status: "PASS",
      gate: "memory_atlas_v1_2_home_multiviewport",
      targetUrl,
      outputDir,
      viewports,
      checks: [
        "five workspace sections have no pairwise overlap",
        "document and workspace sections have no horizontal overflow",
        "workspace and sections remain inside the visible viewport",
        "command palette top, detail, and final safety content are scroll-reachable",
        "home overview first and final sections are scroll-reachable",
        "home direct sections and key nested containers have no horizontal clipping",
        "S06 behavior summaries are Chinese-readable and scroll-reachable",
        "screenshots are nonblank",
        "preview server is released after validation",
      ],
      results,
    };
    writeStatus(payload);
    console.log(JSON.stringify(payload, null, 2));
  } catch (error) {
    if (preview) await stopPreviewServer(preview.server).catch(() => undefined);
    await assertPortClosed().catch(() => undefined);
    const payload = {
      status: "FAIL",
      gate: "memory_atlas_v1_2_home_multiviewport",
      message: error.message,
      details: error.details || null,
      targetUrl,
      outputDir,
      viewports,
      serverLogs: preview?.logs?.join("").slice(-4000) || "",
    };
    writeStatus(payload);
    console.error(JSON.stringify(payload, null, 2));
    process.exitCode = 1;
  }
})();
