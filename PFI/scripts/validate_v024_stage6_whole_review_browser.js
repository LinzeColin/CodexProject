#!/usr/bin/env node
"use strict";

const crypto = require("node:crypto");
const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");
const { URL } = require("node:url");

let playwright;
try {
  playwright = require("playwright");
} catch (error) {
  if (!process.env.PLAYWRIGHT_PACKAGE_PATH) throw error;
  playwright = require(process.env.PLAYWRIGHT_PACKAGE_PATH);
}

const { chromium } = playwright;

const ROOT = path.resolve(__dirname, "..");
const WEB_ROOT = path.join(ROOT, "web");
const REVIEW_DIR = path.join(ROOT, "reports", "pfi_v024", "stage_6", "whole_stage_review");
const SCREENSHOT_DIR = path.join(REVIEW_DIR, "screenshots");
const PLAYWRIGHT_PACKAGE_PATH = process.env.PLAYWRIGHT_PACKAGE_PATH || "";
const PRIMARY_WORKSPACES = Object.freeze([
  "home",
  "accounts",
  "ledger",
  "investment",
  "consumption",
  "sync",
  "recommendations",
  "insights",
  "market_research",
  "settings",
]);
const serverNotFoundPaths = [];

function ensureDirs() {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

function mimeType(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  return {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".svg": "image/svg+xml",
  }[ext] || "application/octet-stream";
}

function startStaticServer() {
  const server = http.createServer((request, response) => {
    try {
      const requestUrl = new URL(request.url || "/", "http://127.0.0.1");
      if (requestUrl.pathname === "/favicon.ico") {
        response.writeHead(204);
        response.end();
        return;
      }
      const requestPath = decodeURIComponent(requestUrl.pathname === "/" ? "/index.html" : requestUrl.pathname);
      const resolved = path.resolve(WEB_ROOT, `.${requestPath}`);
      if (!resolved.startsWith(WEB_ROOT)) {
        response.writeHead(403);
        response.end("Forbidden");
        return;
      }
      const stat = fs.existsSync(resolved) ? fs.statSync(resolved) : null;
      const filePath = stat?.isDirectory() ? path.join(resolved, "index.html") : resolved;
      if (!fs.existsSync(filePath)) {
        serverNotFoundPaths.push(requestPath);
        response.writeHead(404);
        response.end("Not found");
        return;
      }
      response.writeHead(200, { "Content-Type": mimeType(filePath) });
      fs.createReadStream(filePath).pipe(response);
    } catch (error) {
      response.writeHead(500);
      response.end(String(error?.message || error));
    }
  });
  return new Promise((resolve, reject) => {
    server.on("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      resolve({ server, baseUrl: `http://127.0.0.1:${address.port}` });
    });
  });
}

async function waitForReady(page) {
  await page.waitForLoadState("networkidle");
  await page.waitForFunction(() => {
    const shellReady = document.querySelector(".app-shell")?.dataset.state === "ready";
    return shellReady
      && document.body?.dataset.pfiTargetVersion === "v0.2.4"
      && document.body?.dataset.v024Stage6DesignSystem === "phase_6_1"
      && document.body?.dataset.v024Stage6MotionFeedback === "phase_6_2"
      && document.body?.dataset.v024Stage6HapticsSettings === "phase_6_3";
  });
}

async function navigateRoute(page, baseUrl, routeAlias, workspace) {
  await page.goto(`${baseUrl}/index.html#${encodeURIComponent(routeAlias)}`, { waitUntil: "networkidle" });
  await waitForReady(page);
  await page.waitForFunction((expectedWorkspace) => {
    return document.querySelector("#main-workspace")?.dataset.activeWorkspace === expectedWorkspace;
  }, workspace);
}

async function capture(page, file, kind, viewport, screenshots) {
  const filePath = path.join(SCREENSHOT_DIR, file);
  await page.screenshot({ path: filePath, fullPage: true });
  screenshots.push({
    kind,
    file,
    viewport,
    bytes: fs.statSync(filePath).size,
  });
}

function parseRgb(rgb) {
  const values = String(rgb).match(/\d+(\.\d+)?/g) || [];
  return values.slice(0, 3).map(Number);
}

function luminanceFromRgb(rgb) {
  const [r, g, b] = parseRgb(rgb);
  if (![r, g, b].every(Number.isFinite)) return 0;
  return Math.round(0.2126 * r + 0.7152 * g + 0.0722 * b);
}

async function main() {
  ensureDirs();
  const { server, baseUrl } = await startStaticServer();
  const consoleErrors = [];
  const pageErrors = [];
  const httpErrors = [];
  const screenshots = [];
  let browser;
  try {
    browser = await chromium.launch({ headless: true });
    const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });
    page.on("console", (message) => {
      if (message.type() === "error") consoleErrors.push(message.text());
    });
    page.on("pageerror", (error) => pageErrors.push(error.message));
    page.on("response", (response) => {
      if (response.status() >= 400) {
        httpErrors.push({ url: response.url(), status: response.status() });
      }
    });

    await navigateRoute(page, baseUrl, "/home", "home");
    const desktopState = await page.evaluate(() => {
      const main = document.querySelector("#main-workspace");
      const settingsConsole = document.querySelector("[data-settings-feedback-console]");
      const primaryWorkspaces = Array.from(document.querySelectorAll('[data-primary-entry="true"]')).map((node) => node.dataset.workspace);
      const phonePreview = document.querySelector(".phone-preview, .mobile-preview-frame, [data-phone-preview]");
      const bodyStyle = getComputedStyle(document.body);
      return {
        primaryWorkspaces,
        bodyBackgroundColor: bodyStyle.backgroundColor,
        targetVersion: document.body.dataset.pfiTargetVersion,
        colorSchemeMeta: document.querySelector('meta[name="color-scheme"]')?.getAttribute("content") || "",
        activeWorkspace: main?.dataset.activeWorkspace || "",
        settingsFeedbackConsoleHidden: Boolean(settingsConsole?.hidden),
        phonePreviewVisible: Boolean(phonePreview && getComputedStyle(phonePreview).display !== "none"),
      };
    });
    await capture(page, "desktop_light_home.png", "desktop_light_home", { width: 1440, height: 960 }, screenshots);

    await page.setViewportSize({ width: 390, height: 844 });
    await navigateRoute(page, baseUrl, "/home", "home");
    const mobileState = await page.evaluate(() => ({
      width: window.innerWidth,
      horizontalOverflowPx: Math.max(0, document.documentElement.scrollWidth - window.innerWidth),
      bottomNavVisible: getComputedStyle(document.querySelector(".mobile-bottom-nav")).display !== "none",
    }));
    await capture(page, "mobile_responsive.png", "mobile_responsive", { width: 390, height: 844 }, screenshots);

    await page.setViewportSize({ width: 1440, height: 960 });
    await navigateRoute(page, baseUrl, "/settings", "settings");
    const settingsState = await page.evaluate(() => {
      const settingsConsole = document.querySelector("[data-settings-feedback-console]");
      const toggles = Array.from(document.querySelectorAll("[data-feedback-toggle]")).map((node) => ({
        id: node.getAttribute("data-feedback-toggle"),
        phase: node.dataset.v024FeedbackSetting || "",
        checked: Boolean(node.checked),
      }));
      return {
        settingsFeedbackConsoleVisible: Boolean(settingsConsole && !settingsConsole.hidden),
        toggles,
        hapticCapability: document.body.dataset.v024HapticCapability || "",
        hapticDegraded: document.body.dataset.v024HapticDegraded || "",
      };
    });
    await capture(page, "settings_feedback_isolation.png", "settings_feedback_isolation", { width: 1440, height: 960 }, screenshots);

    const bodyBackgroundLuminance = luminanceFromRgb(desktopState.bodyBackgroundColor);
    const toggleIds = settingsState.toggles.map((item) => item.id).sort();
    const validation = {
      schema: "PFIV024Stage6WholeReviewBrowserValidationV1",
      target_version: "v0.2.4",
      source_package_version: "v0.2.3-repair",
      stage: "Stage 6",
      review_id: "stage_6_whole_review",
      status: "pass",
      source: `${baseUrl}/index.html`,
      playwright_package_path: PLAYWRIGHT_PACKAGE_PATH,
      primary_entry_count: desktopState.primaryWorkspaces.length,
      primary_workspaces: desktopState.primaryWorkspaces,
      default_light_ui: desktopState.targetVersion === "v0.2.4"
        && desktopState.colorSchemeMeta === "light"
        && bodyBackgroundLuminance >= 210,
      body_background_color: desktopState.bodyBackgroundColor,
      body_background_luminance: bodyBackgroundLuminance,
      desktop_light_home_screenshot: screenshots.some((item) => item.file === "desktop_light_home.png"),
      mobile_responsive_screenshot: screenshots.some((item) => item.file === "mobile_responsive.png"),
      mobile_horizontal_overflow_px: mobileState.horizontalOverflowPx,
      mobile_bottom_nav_visible: mobileState.bottomNavVisible,
      desktop_phone_preview_frame_visible: desktopState.phonePreviewVisible,
      settings_feedback_console_hidden_on_home: desktopState.settingsFeedbackConsoleHidden,
      settings_feedback_console_visible_on_settings: settingsState.settingsFeedbackConsoleVisible,
      feedback_toggle_ids: toggleIds,
      haptic_capability_detected: Boolean(settingsState.hapticCapability),
      haptic_capability: settingsState.hapticCapability || "unsupported",
      haptic_degrades_visually_when_unsupported: settingsState.hapticCapability === "supported"
        || settingsState.hapticDegraded === "visual_feedback",
      console_errors: consoleErrors,
      page_errors: pageErrors,
      http_errors: httpErrors,
      server_not_found_paths: serverNotFoundPaths,
      screenshots,
      generated_at: new Date().toISOString(),
      validation_hash: crypto.createHash("sha256").update(JSON.stringify({
        desktopState,
        mobileState,
        settingsState,
        screenshots: screenshots.map((item) => [item.kind, item.file, item.bytes]),
      })).digest("hex"),
    };

    const failures = [];
    if (validation.primary_entry_count !== 10) failures.push(`primary_entry_count=${validation.primary_entry_count}`);
    if (JSON.stringify(validation.primary_workspaces) !== JSON.stringify(PRIMARY_WORKSPACES)) failures.push("primary_workspaces mismatch");
    if (!validation.default_light_ui) failures.push("default_light_ui=false");
    if (!validation.desktop_light_home_screenshot) failures.push("missing desktop screenshot");
    if (!validation.mobile_responsive_screenshot) failures.push("missing mobile screenshot");
    if (validation.mobile_horizontal_overflow_px > 2) failures.push(`mobile overflow=${validation.mobile_horizontal_overflow_px}`);
    if (validation.desktop_phone_preview_frame_visible) failures.push("desktop phone preview frame visible");
    if (!validation.settings_feedback_console_hidden_on_home) failures.push("feedback console visible on home");
    if (!validation.settings_feedback_console_visible_on_settings) failures.push("feedback console hidden on settings");
    if (JSON.stringify(toggleIds) !== JSON.stringify(["haptic", "motion", "sound"])) failures.push("feedback toggles mismatch");
    if (!validation.haptic_capability_detected) failures.push("missing haptic capability dataset");
    if (!validation.haptic_degrades_visually_when_unsupported) failures.push("haptic unsupported degradation missing");
    if (consoleErrors.length || pageErrors.length || httpErrors.length || serverNotFoundPaths.length) failures.push("browser errors present");
    if (failures.length) validation.status = "fail";
    validation.failures = failures;

    fs.writeFileSync(path.join(REVIEW_DIR, "browser_validation.json"), `${JSON.stringify(validation, null, 2)}\n`);
    console.log(JSON.stringify({
      status: validation.status,
      screenshots: screenshots.length,
      review_dir: REVIEW_DIR,
      failures,
    }, null, 2));
    if (validation.status !== "pass") process.exitCode = 1;
  } finally {
    if (browser) await browser.close();
    server.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
