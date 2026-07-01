#!/usr/bin/env node
"use strict";

const crypto = require("node:crypto");
const fs = require("node:fs");
const net = require("node:net");
const os = require("node:os");
const path = require("node:path");
const { execFileSync, spawn } = require("node:child_process");

let playwright;
try {
  playwright = require("playwright");
} catch (error) {
  if (!process.env.PLAYWRIGHT_PACKAGE_PATH) throw error;
  playwright = require(process.env.PLAYWRIGHT_PACKAGE_PATH);
}

const { chromium } = playwright;

const REPO_ROOT = path.resolve(__dirname, "..", "..");
const PFI_ROOT = path.join(REPO_ROOT, "PFI");
const PHASE81_DIR = path.join(PFI_ROOT, "reports", "pfi_v024", "stage_8", "phase_8_1");
const PHASE_DIR = path.join(PFI_ROOT, "reports", "pfi_v024", "stage_8", "phase_8_2");
const SCREENSHOT_DIR = path.join(PHASE_DIR, "screenshots");
const VERSION_QUERY =
  "pfi_app_version=0.2.3&pfi_build=pfi-v024-stage2-phase22&pfi_ui_contract=PFI-V024-STAGE2-ENTRY-CONSISTENCY";
const EXPECTED = {
  targetVersion: "v0.2.4",
  sourcePackageVersion: "v0.2.3-repair",
  repairLabel: "PFI v0.2.3 Repair",
  buildId: "pfi-v024-stage2-phase22",
  uiContractVersion: "PFI-V024-STAGE2-ENTRY-CONSISTENCY",
};
const PRIMARY_ROUTES = Object.freeze([
  { screenshotId: "primary_01_home", label: "首页总览", routeAlias: "/home", workspace: "home" },
  { screenshotId: "primary_02_accounts", label: "账户与资产", routeAlias: "/accounts", workspace: "accounts" },
  { screenshotId: "primary_03_ledger", label: "账本流水", routeAlias: "/ledger", workspace: "ledger" },
  { screenshotId: "primary_04_investment", label: "投资管理", routeAlias: "/investment", workspace: "investment" },
  { screenshotId: "primary_05_consumption", label: "消费管理", routeAlias: "/consumption", workspace: "consumption" },
  { screenshotId: "primary_06_sources_upload", label: "数据源与上传", routeAlias: "/sources-upload", workspace: "sync" },
  { screenshotId: "primary_07_review", label: "建议与复盘", routeAlias: "/review", workspace: "recommendations" },
  { screenshotId: "primary_08_reports", label: "报告与洞察", routeAlias: "/reports", workspace: "insights" },
  { screenshotId: "primary_09_market_research", label: "市场与研究", routeAlias: "/market-research", workspace: "market_research" },
  { screenshotId: "primary_10_settings", label: "设置", routeAlias: "/settings", workspace: "settings" },
]);
const PLAYWRIGHT_PACKAGE_PATH = process.env.PLAYWRIGHT_PACKAGE_PATH || "";

function ensureDirs() {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

function run(command, args, options = {}) {
  return execFileSync(command, args, {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
    ...options,
  }).trim();
}

function runStatus(command, args, options = {}) {
  try {
    const stdout = run(command, args, options);
    return { exitCode: 0, stdout, stderr: "" };
  } catch (error) {
    return {
      exitCode: typeof error.status === "number" ? error.status : 1,
      stdout: String(error.stdout || "").trim(),
      stderr: String(error.stderr || error.message || "").trim(),
    };
  }
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf-8"));
}

function writeJson(fileName, payload) {
  fs.writeFileSync(path.join(PHASE_DIR, fileName), `${JSON.stringify(payload, null, 2)}\n`);
}

function readText(filePath) {
  return fs.readFileSync(filePath, "utf8").trim();
}

function relativePath(filePath) {
  return path.relative(REPO_ROOT, filePath).split(path.sep).join("/");
}

function fileSha256(filePath) {
  return crypto.createHash("sha256").update(fs.readFileSync(filePath)).digest("hex");
}

function screenshotInfo({ filePath, screenshotId, group, label, routeAlias, workspace, viewport, source }) {
  return {
    screenshot_id: screenshotId,
    group,
    label,
    route_alias: routeAlias || "",
    workspace: workspace || "",
    viewport,
    source,
    path: relativePath(filePath),
    bytes: fs.statSync(filePath).size,
    sha256: fileSha256(filePath),
  };
}

function healthyPort(port) {
  const result = runStatus("curl", ["-s", "-o", "/dev/null", "-w", "%{http_code}", `http://127.0.0.1:${port}/_stcore/health`]);
  return result.exitCode === 0 && result.stdout === "200";
}

function portInUse(port) {
  return runStatus("lsof", [`-iTCP:${port}`, "-sTCP:LISTEN"]).exitCode === 0;
}

function appPython() {
  const localVenv = path.join(PFI_ROOT, ".venv", "bin", "python");
  if (fs.existsSync(localVenv)) return localVenv;
  return run("zsh", ["-lc", "source scripts/pfiRuntime.sh && pfi_os_ensure_app_python \"$PWD\""], { cwd: PFI_ROOT });
}

function waitForService(port, child) {
  return new Promise((resolve, reject) => {
    const startedAt = Date.now();
    const timer = setInterval(() => {
      if (child.exitCode !== null) {
        clearInterval(timer);
        reject(new Error(`temporary Streamlit exited before healthy; exit=${child.exitCode}`));
        return;
      }
      if (healthyPort(port)) {
        clearInterval(timer);
        resolve();
        return;
      }
      if (Date.now() - startedAt > 60_000) {
        clearInterval(timer);
        reject(new Error(`temporary Streamlit was not healthy within 60s on port ${port}`));
      }
    }, 1000);
  });
}

async function startTemporaryService() {
  let port = 8601;
  while (portInUse(port)) port += 1;
  const python = appPython();
  const logPath = path.join(PHASE_DIR, "streamlit.log");
  const log = fs.openSync(logPath, "a");
  const args = [
    "-m", "streamlit", "run", "src/pfi_os/app/streamlit_app.py",
    "--server.port", String(port),
    "--server.address", "127.0.0.1",
    "--server.headless", "true",
    "--server.fileWatcherType", "none",
    "--browser.gatherUsageStats", "false",
  ];
  const child = spawn(python, args, {
    cwd: PFI_ROOT,
    detached: false,
    stdio: ["ignore", log, log],
    env: {
      ...process.env,
      PYTHONPATH: path.join(PFI_ROOT, "src"),
      PFI_UI_V2: "1",
      PFI_START_OPEN_BROWSER: "0",
    },
  });
  await waitForService(port, child);
  return {
    url: `http://127.0.0.1:${port}`,
    port,
    pid: child.pid,
    project_root: PFI_ROOT,
    health: "ok",
    current_checkout_temporary_service: true,
    log_path: relativePath(logPath),
    process: child,
  };
}

async function stopTemporaryService(service) {
  if (!service?.process) return;
  service.process.kill("SIGTERM");
  await new Promise((resolve) => setTimeout(resolve, 500));
  if (service.process.exitCode === null) {
    service.process.kill("SIGKILL");
  }
}

function readAppBinding(appPath) {
  const rootFile = path.join(appPath, "Contents", "Resources", "PFI_PROJECT_ROOT");
  const executable = path.join(appPath, "Contents", "MacOS", "PFI");
  const exists = fs.existsSync(appPath);
  const projectRoot = exists && fs.existsSync(rootFile) ? readText(rootFile) : "";
  const dryRun = exists && fs.existsSync(executable)
    ? runStatus(executable, [], { env: { ...process.env, PFI_APP_LAUNCH_DRY_RUN: "1" } })
    : { exitCode: 1, stdout: "", stderr: "missing app executable" };
  return {
    path: appPath,
    exists,
    project_root: projectRoot,
    dry_run_exit_code: dryRun.exitCode,
    dry_run_stdout: dryRun.stdout,
    dry_run_stderr: dryRun.stderr,
  };
}

function appBindings() {
  const home = os.homedir();
  const applications = readAppBinding("/Applications/PFI.app");
  const downloads = readAppBinding(path.join(home, "Downloads", "PFI.app"));
  return {
    applications,
    downloads,
    selected: applications.project_root === PFI_ROOT && applications.dry_run_exit_code === 0 ? applications : downloads,
    applications_project_root: applications.project_root,
    downloads_project_root: downloads.project_root,
    applications_app_points_to_current_checkout:
      applications.exists && applications.project_root === PFI_ROOT && applications.dry_run_exit_code === 0,
    downloads_app_points_to_current_checkout:
      downloads.exists && downloads.project_root === PFI_ROOT && downloads.dry_run_exit_code === 0,
  };
}

function ignoredHttpError(url) {
  return url.includes("favicon") || url.includes("/_stcore/health");
}

function ignoredConsoleError(text) {
  return text.includes("favicon");
}

async function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function waitForPfiFrame(page) {
  for (let attempt = 0; attempt < 160; attempt += 1) {
    for (const frame of page.frames()) {
      const ok = await frame
        .evaluate(() => {
          return Boolean(
            document.querySelector("[data-pfi-entry-version-strip]") ||
              typeof window.PFI_READ_STAGE2_ENTRY_AUDIT === "function"
          );
        })
        .catch(() => false);
      if (ok) return frame;
    }
    await sleep(125);
  }
  throw new Error("Timed out waiting for PFI Web Shell iframe");
}

async function waitForFrameReady(frame) {
  await frame.waitForFunction(() => {
    return document.querySelector(".app-shell")?.dataset.state === "ready"
      && typeof window.PFI_READ_STAGE2_ENTRY_AUDIT === "function";
  });
}

async function captureEntryPath({ browser, name, url, screenshotId, group, viewport, source, binding, collector }) {
  const context = await browser.newContext({ viewport });
  const page = await context.newPage();
  page.on("console", (message) => {
    if (message.type() === "error" && !ignoredConsoleError(message.text())) {
      collector.consoleErrors.push(message.text());
    }
  });
  page.on("pageerror", (error) => collector.pageErrors.push(error.message));
  page.on("response", (response) => {
    if (response.status() >= 400 && !ignoredHttpError(response.url())) {
      collector.httpErrors.push({ url: response.url(), status: response.status() });
    }
  });

  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60_000 });
  const frame = await waitForPfiFrame(page);
  await waitForFrameReady(frame);
  await page.waitForTimeout(750);
  const framePayload = await frame.evaluate(() => {
    const audit = typeof window.PFI_READ_STAGE2_ENTRY_AUDIT === "function"
      ? window.PFI_READ_STAGE2_ENTRY_AUDIT()
      : {};
    const read = (selector) => document.querySelector(selector)?.textContent?.trim() || "";
    return {
      entry_audit: audit,
      active_workspace: document.querySelector("#main-workspace")?.dataset.activeWorkspace || "",
      active_route: document.querySelector("#main-workspace")?.dataset.routeAlias || "",
      visible_entry_strip: {
        repair_label: read("[data-pfi-entry-repair-label]"),
        build_id: read("[data-pfi-entry-build-id]"),
        bundle_hash: read("[data-pfi-entry-bundle-hash]"),
        ui_contract: read("[data-pfi-entry-ui-contract]"),
      },
    };
  });
  const screenshotPath = path.join(SCREENSHOT_DIR, `${screenshotId}.png`);
  await page.screenshot({ path: screenshotPath, fullPage: true });
  const screenshot = screenshotInfo({
    filePath: screenshotPath,
    screenshotId,
    group,
    label: name,
    routeAlias: framePayload.active_route,
    workspace: framePayload.active_workspace,
    viewport,
    source,
  });
  await context.close();

  const audit = framePayload.entry_audit || {};
  return {
    ok:
      audit.targetVersion === EXPECTED.targetVersion &&
      audit.sourcePackageVersion === EXPECTED.sourcePackageVersion &&
      audit.repairLabel === EXPECTED.repairLabel &&
      audit.buildId === EXPECTED.buildId &&
      audit.uiContractVersion === EXPECTED.uiContractVersion &&
      Boolean(audit.webBundleHash) &&
      screenshot.bytes > 20_000,
    url,
    screenshot,
    app_binding: binding || undefined,
    ...framePayload,
  };
}

async function capturePrimaryEntries({ browser, url, collector }) {
  const viewport = { width: 1440, height: 1000 };
  const context = await browser.newContext({ viewport });
  const page = await context.newPage();
  page.on("console", (message) => {
    if (message.type() === "error" && !ignoredConsoleError(message.text())) {
      collector.consoleErrors.push(message.text());
    }
  });
  page.on("pageerror", (error) => collector.pageErrors.push(error.message));
  page.on("response", (response) => {
    if (response.status() >= 400 && !ignoredHttpError(response.url())) {
      collector.httpErrors.push({ url: response.url(), status: response.status() });
    }
  });

  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60_000 });
  const frame = await waitForPfiFrame(page);
  await waitForFrameReady(frame);
  await page.waitForTimeout(500);

  const captured = [];
  for (const route of PRIMARY_ROUTES) {
    await frame.locator(`[data-primary-entry="true"][data-route-alias="${route.routeAlias}"]`).click();
    await frame.waitForFunction((workspace) => {
      return document.querySelector("#main-workspace")?.dataset.activeWorkspace === workspace;
    }, route.workspace);
    await page.waitForTimeout(300);
    const screenshotPath = path.join(SCREENSHOT_DIR, `${route.screenshotId}.png`);
    await page.screenshot({ path: screenshotPath, fullPage: true });
    captured.push(screenshotInfo({
      filePath: screenshotPath,
      screenshotId: route.screenshotId,
      group: "primary_entries",
      label: route.label,
      routeAlias: route.routeAlias,
      workspace: route.workspace,
      viewport,
      source: url,
    }));
  }
  await context.close();
  return captured;
}

function parseRgb(value) {
  const match = String(value || "").match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/i);
  if (!match) return null;
  return [Number(match[1]), Number(match[2]), Number(match[3])];
}

function luminance(rgb) {
  if (!rgb) return 0;
  return (0.2126 * rgb[0]) + (0.7152 * rgb[1]) + (0.0722 * rgb[2]);
}

async function captureMobileResponsive({ browser, url, collector }) {
  const viewport = { width: 390, height: 844 };
  const context = await browser.newContext({
    viewport,
    isMobile: true,
    hasTouch: true,
  });
  const page = await context.newPage();
  page.on("console", (message) => {
    if (message.type() === "error" && !ignoredConsoleError(message.text())) {
      collector.consoleErrors.push(message.text());
    }
  });
  page.on("pageerror", (error) => collector.pageErrors.push(error.message));
  page.on("response", (response) => {
    if (response.status() >= 400 && !ignoredHttpError(response.url())) {
      collector.httpErrors.push({ url: response.url(), status: response.status() });
    }
  });

  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60_000 });
  const frame = await waitForPfiFrame(page);
  await waitForFrameReady(frame);
  await page.waitForTimeout(750);
  const mobileState = await frame.evaluate(() => {
    const root = document.documentElement;
    const body = document.body;
    const overflow = Math.max(
      0,
      root.scrollWidth - root.clientWidth,
      body.scrollWidth - body.clientWidth
    );
    return {
      horizontal_overflow_px: overflow,
      bottom_nav_visible: getComputedStyle(document.querySelector(".mobile-bottom-nav")).display !== "none",
      active_workspace: document.querySelector("#main-workspace")?.dataset.activeWorkspace || "",
      route_alias: document.querySelector("#main-workspace")?.dataset.routeAlias || "",
    };
  });
  const screenshotPath = path.join(SCREENSHOT_DIR, "mobile_responsive.png");
  await page.screenshot({ path: screenshotPath, fullPage: true });
  const screenshot = screenshotInfo({
    filePath: screenshotPath,
    screenshotId: "mobile_responsive",
    group: "mobile",
    label: "移动端响应式",
    routeAlias: mobileState.route_alias,
    workspace: mobileState.active_workspace,
    viewport,
    source: url,
  });
  await context.close();
  return { state: mobileState, screenshot };
}

async function captureDesktopAllPages({ browser, primaryScreenshots }) {
  const viewport = { width: 1600, height: 2400 };
  const context = await browser.newContext({ viewport });
  const page = await context.newPage();
  const figures = primaryScreenshots.map((item) => {
    const absolute = path.join(REPO_ROOT, item.path);
    const dataUrl = `data:image/png;base64,${fs.readFileSync(absolute).toString("base64")}`;
    return [
      "<figure>",
      `<figcaption>${item.screenshot_id} · ${item.label}</figcaption>`,
      `<img src="${dataUrl}" alt="${item.label}">`,
      "</figure>",
    ].join("");
  }).join("");
  await page.setContent([
    "<!doctype html>",
    "<html>",
    "<head>",
    "<meta charset=\"utf-8\">",
    "<style>",
    "body{margin:0;padding:24px;background:#f7f8fb;color:#1f2937;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}",
    "h1{font-size:22px;margin:0 0 18px;}",
    ".grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;}",
    "figure{margin:0;background:white;border:1px solid #d8dee8;border-radius:8px;padding:10px;box-shadow:0 1px 2px rgba(15,23,42,.08);}",
    "figcaption{font-size:12px;margin:0 0 8px;color:#334155;}",
    "img{width:100%;height:auto;display:block;border:1px solid #e5e7eb;border-radius:6px;}",
    "</style>",
    "</head>",
    "<body>",
    "<h1>PFI v0.2.4 Stage 8.2 · 10 个一级入口截图索引</h1>",
    `<section class="grid">${figures}</section>`,
    "</body>",
    "</html>",
  ].join(""), { waitUntil: "load" });
  await page.waitForLoadState("networkidle").catch(() => undefined);
  const screenshotPath = path.join(SCREENSHOT_DIR, "desktop_all_pages.png");
  await page.screenshot({ path: screenshotPath, fullPage: true });
  await context.close();
  return screenshotInfo({
    filePath: screenshotPath,
    screenshotId: "desktop_all_pages",
    group: "desktop_all_pages",
    label: "10 个一级入口截图索引",
    routeAlias: "",
    workspace: "",
    viewport,
    source: "generated_contact_sheet_from_phase82_screenshots",
  });
}

async function inspectDesktopLightUi({ browser, url, collector }) {
  const viewport = { width: 1440, height: 1000 };
  const context = await browser.newContext({ viewport });
  const page = await context.newPage();
  page.on("console", (message) => {
    if (message.type() === "error" && !ignoredConsoleError(message.text())) {
      collector.consoleErrors.push(message.text());
    }
  });
  page.on("pageerror", (error) => collector.pageErrors.push(error.message));
  page.on("response", (response) => {
    if (response.status() >= 400 && !ignoredHttpError(response.url())) {
      collector.httpErrors.push({ url: response.url(), status: response.status() });
    }
  });
  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60_000 });
  const frame = await waitForPfiFrame(page);
  await waitForFrameReady(frame);
  const state = await frame.evaluate(() => {
    const appShell = document.querySelector(".app-shell") || document.body;
    const style = getComputedStyle(appShell);
    const bodyStyle = getComputedStyle(document.body);
    return {
      app_shell_background: style.backgroundColor,
      body_background: bodyStyle.backgroundColor,
      color_scheme_meta: document.querySelector('meta[name="color-scheme"]')?.content || "",
      primary_entry_count: document.querySelectorAll('[data-primary-entry="true"]').length,
    };
  });
  await context.close();
  return {
    ...state,
    light_ui: state.color_scheme_meta.includes("light")
      || luminance(parseRgb(state.app_shell_background)) >= 180
      || luminance(parseRgb(state.body_background)) >= 180,
  };
}

function groupCounts(screenshots) {
  const groups = {};
  for (const item of screenshots) {
    if (!groups[item.group]) groups[item.group] = { count: 0, bytes: 0 };
    groups[item.group].count += 1;
    groups[item.group].bytes += item.bytes;
  }
  return groups;
}

function buildChangedFiles() {
  return [
    "PFI/CHANGELOG.md",
    "PFI/HANDOFF.md",
    "PFI/README.md",
    "PFI/docs/pfi_v024/RUN_CONTRACT.md",
    "PFI/docs/pfi_v024/STAGE8_E2E_ACCEPTANCE.md",
    "PFI/reports/pfi_v024/stage_8/phase_8_2/app_entry_validation.json",
    "PFI/reports/pfi_v024/stage_8/phase_8_2/browser_validation.json",
    "PFI/reports/pfi_v024/stage_8/phase_8_2/changed_files.txt",
    "PFI/reports/pfi_v024/stage_8/phase_8_2/evidence.json",
    "PFI/reports/pfi_v024/stage_8/phase_8_2/risk_and_rollback.md",
    "PFI/reports/pfi_v024/stage_8/phase_8_2/screenshot_index.json",
    "PFI/reports/pfi_v024/stage_8/phase_8_2/screenshots/app_home.png",
    "PFI/reports/pfi_v024/stage_8/phase_8_2/screenshots/desktop_all_pages.png",
    "PFI/reports/pfi_v024/stage_8/phase_8_2/screenshots/localhost_home.png",
    "PFI/reports/pfi_v024/stage_8/phase_8_2/screenshots/mobile_responsive.png",
    ...PRIMARY_ROUTES.map((route) => `PFI/reports/pfi_v024/stage_8/phase_8_2/screenshots/${route.screenshotId}.png`),
    "PFI/reports/pfi_v024/stage_8/phase_8_2/streamlit.log",
    "PFI/reports/pfi_v024/stage_8/phase_8_2/terminal.log",
    "PFI/scripts/validate_v024_stage8_phase82_screenshots.js",
    "PFI/src/pfi_v02/stage_v024_stage8_e2e_acceptance.py",
    "PFI/tests/test_v024_stage8_phase81_e2e_auto_acceptance.py",
    "PFI/tests/test_v024_stage8_phase82_screenshot_acceptance.py",
    "PFI/功能清单.md",
    "PFI/开发记录.md",
    "PFI/模型参数文件.md",
  ];
}

function writeSupportFiles(changedFiles, generatedAt, service, status) {
  fs.writeFileSync(path.join(PHASE_DIR, "changed_files.txt"), `${changedFiles.join("\n")}\n`);
  fs.writeFileSync(path.join(PHASE_DIR, "risk_and_rollback.md"), [
    "# Stage 8 Phase 8.2 Risk and Rollback",
    "",
    "## Risk",
    "",
    "- 本轮只执行 Stage 8 Phase 8.2 截图验收。",
    "- 本轮不执行 Phase 8.3 人工验收、Stage 8 whole-stage review、Stage 9 或 GitHub main upload。",
    "- 本轮不重装 app bundle，不写入或改写真实财务数据。",
    "",
    "## Rollback",
    "",
    "如截图验收失败，保留截图和 browser_validation.json 后定位 app/localhost 入口、bundle hash 或响应式问题。",
    "本轮变更可通过回退 Stage 8.2 合同、脚本、测试、文档和 evidence 文件撤销。",
    "",
  ].join("\n"));
  fs.writeFileSync(path.join(PHASE_DIR, "terminal.log"), [
    "Stage 8 Phase 8.2 screenshot acceptance validation log",
    "",
    "RED:",
    "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage8_phase82_screenshot_acceptance.py -q",
    "5 failed: missing phase82 contract, screenshot evidence pack, screenshot index, browser validation, and docs.",
    "",
    "Generation:",
    "PLAYWRIGHT_PACKAGE_PATH=... PATH=... node PFI/scripts/validate_v024_stage8_phase82_screenshots.js",
    `generated_at=${generatedAt}`,
    `service_url=${service.url}`,
    `service_pid=${service.pid}`,
    `service_project_root=${service.project_root}`,
    `browser_validation=${status}`,
    "",
    "Final validation commands are recorded in the run terminal after the GREEN pass.",
    "",
  ].join("\n"));
}

async function main() {
  ensureDirs();
  const generatedAt = new Date().toISOString();
  const phase81Evidence = readJson(path.join(PHASE81_DIR, "evidence.json"));
  const service = await startTemporaryService();
  const publicService = Object.fromEntries(
    Object.entries(service).filter(([key]) => key !== "process")
  );
  const bindings = appBindings();
  const selectedApp = bindings.selected || bindings.downloads;
  const urls = {
    localhost: `${service.url}/?${VERSION_QUERY}&pfi_entry=localhost`,
    app: `${service.url}/?${VERSION_QUERY}&pfi_entry=app&pfi_app_path=${encodeURIComponent(selectedApp.path)}`,
  };
  const collector = { consoleErrors: [], pageErrors: [], httpErrors: [] };
  let browser;
  try {
    browser = await chromium.launch({ headless: true });
    const appPath = await captureEntryPath({
      browser,
      name: "app",
      url: urls.app,
      screenshotId: "app_home",
      group: "app",
      viewport: { width: 1440, height: 1000 },
      source: urls.app,
      binding: selectedApp,
      collector,
    });
    const localhostPath = await captureEntryPath({
      browser,
      name: "localhost",
      url: urls.localhost,
      screenshotId: "localhost_home",
      group: "localhost",
      viewport: { width: 1440, height: 1000 },
      source: urls.localhost,
      collector,
    });
    const primaryScreenshots = await capturePrimaryEntries({
      browser,
      url: urls.localhost,
      collector,
    });
    const mobile = await captureMobileResponsive({
      browser,
      url: urls.localhost,
      collector,
    });
    const desktopAllPages = await captureDesktopAllPages({ browser, primaryScreenshots });
    const lightUi = await inspectDesktopLightUi({ browser, url: urls.localhost, collector });
    const screenshots = [
      appPath.screenshot,
      localhostPath.screenshot,
      ...primaryScreenshots,
      mobile.screenshot,
      desktopAllPages,
    ];
    const groups = groupCounts(screenshots);
    const appHash = appPath.entry_audit.webBundleHash || "";
    const localhostHash = localhostPath.entry_audit.webBundleHash || "";
    const screenshotIndexStatus =
      screenshots.every((item) => item.bytes > 20_000 && /^[0-9a-f]{64}$/.test(item.sha256))
      && groups.app?.count === 1
      && groups.localhost?.count === 1
      && groups.primary_entries?.count === 10
      && groups.mobile?.count >= 1
      ? "pass"
      : "fail";
    const appLocalhostSameBundleHash = Boolean(appHash) && appHash === localhostHash;
    const appEntryStatus =
      appPath.ok
      && localhostPath.ok
      && appLocalhostSameBundleHash
      && Boolean(selectedApp.exists && selectedApp.project_root === PFI_ROOT && selectedApp.dry_run_exit_code === 0)
      ? "pass"
      : "fail";
    const browserStatus =
      screenshotIndexStatus === "pass"
      && appEntryStatus === "pass"
      && lightUi.light_ui
      && mobile.state.horizontal_overflow_px === 0
      && collector.consoleErrors.length === 0
      && collector.pageErrors.length === 0
      && collector.httpErrors.length === 0
      ? "pass"
      : "fail";

    const screenshotIndex = {
      schema: "PFIV024Stage8Phase82ScreenshotIndexV1",
      target_version: EXPECTED.targetVersion,
      source_package_version: EXPECTED.sourcePackageVersion,
      stage: "Stage 8",
      phase_id: "8.2",
      status: screenshotIndexStatus,
      screenshot_count: screenshots.length,
      groups,
      screenshots,
      generated_at: generatedAt,
    };
    const appEntryValidation = {
      schema: "PFIV024Stage8Phase82AppEntryValidationV1",
      target_version: appPath.entry_audit.targetVersion,
      source_package_version: appPath.entry_audit.sourcePackageVersion,
      repair_label: appPath.entry_audit.repairLabel,
      build_id: appPath.entry_audit.buildId,
      ui_contract_version: appPath.entry_audit.uiContractVersion,
      status: appEntryStatus,
      app_url: urls.app,
      localhost_url: urls.localhost,
      app_bundle_hash: appHash,
      localhost_bundle_hash: localhostHash,
      app_localhost_same_bundle_hash: appLocalhostSameBundleHash,
      selected_app_path: selectedApp.path,
      selected_app_points_to_current_checkout:
        Boolean(selectedApp.exists && selectedApp.project_root === PFI_ROOT && selectedApp.dry_run_exit_code === 0),
      applications_app_points_to_current_checkout: bindings.applications_app_points_to_current_checkout,
      downloads_app_points_to_current_checkout: bindings.downloads_app_points_to_current_checkout,
      bindings,
      app_screenshot: appPath.screenshot.path,
      localhost_screenshot: localhostPath.screenshot.path,
      generated_at: generatedAt,
    };
    const browserValidation = {
      schema: "PFIV024Stage8Phase82BrowserValidationV1",
      target_version: EXPECTED.targetVersion,
      source_package_version: EXPECTED.sourcePackageVersion,
      stage: "Stage 8",
      phase_id: "8.2",
      phase_name: "截图验收",
      status: browserStatus,
      playwright_package_path: PLAYWRIGHT_PACKAGE_PATH,
      service: publicService,
      app_screenshot_captured: appPath.screenshot.bytes > 20_000,
      localhost_screenshot_captured: localhostPath.screenshot.bytes > 20_000,
      primary_entry_screenshot_count: primaryScreenshots.length,
      mobile_responsive_screenshot_captured: mobile.screenshot.bytes > 20_000,
      desktop_all_pages_screenshot_captured: desktopAllPages.bytes > 20_000,
      app_localhost_same_bundle_hash: appLocalhostSameBundleHash,
      desktop_light_ui: lightUi.light_ui,
      desktop_light_ui_state: lightUi,
      mobile_horizontal_overflow_px: mobile.state.horizontal_overflow_px,
      mobile_bottom_nav_visible: mobile.state.bottom_nav_visible,
      console_errors: collector.consoleErrors,
      page_errors: collector.pageErrors,
      http_errors: collector.httpErrors,
      phase_8_3_started: false,
      stage_8_whole_review_complete: false,
      github_main_uploaded: false,
      stage_9_started: false,
      generated_at: generatedAt,
      validation_hash: crypto.createHash("sha256").update(JSON.stringify({
        screenshots: screenshots.map((item) => [item.screenshot_id, item.sha256, item.bytes]),
        appHash,
        localhostHash,
        mobile: mobile.state,
      })).digest("hex"),
    };
    const changedFiles = buildChangedFiles();
    const evidence = {
      schema: "PFIV024Stage8Phase82EvidenceV1",
      version: "v0.2.3-repair",
      target_version: EXPECTED.targetVersion,
      source_package_version: EXPECTED.sourcePackageVersion,
      stage: "Stage 8",
      stage_name: "端到端浏览器与 app 验收",
      phase_id: "8.2",
      phase_name: "截图验收",
      status: browserStatus === "pass" ? "candidate_pass" : "fail",
      current_phase_only: true,
      phase_8_1_verified: phase81Evidence.status === "candidate_pass"
        && phase81Evidence.route_click_test_passed === true
        && phase81Evidence.entry_version_test_passed === true
        && phase81Evidence.data_state_test_passed === true
        && phase81Evidence.report_center_test_passed === true,
      task_ids: ["T8.2.1", "T8.2.2", "T8.2.3", "T8.2.4"],
      app_screenshot_captured: browserValidation.app_screenshot_captured,
      localhost_screenshot_captured: browserValidation.localhost_screenshot_captured,
      primary_entry_screenshot_count: browserValidation.primary_entry_screenshot_count,
      mobile_responsive_screenshot_captured: browserValidation.mobile_responsive_screenshot_captured,
      app_localhost_same_bundle_hash: appLocalhostSameBundleHash,
      browser_validation: relativePath(path.join(PHASE_DIR, "browser_validation.json")),
      screenshot_index: relativePath(path.join(PHASE_DIR, "screenshot_index.json")),
      app_entry_validation: relativePath(path.join(PHASE_DIR, "app_entry_validation.json")),
      screenshots: screenshots.map((item) => item.path),
      phase_8_3_started: false,
      stage_8_whole_review_complete: false,
      github_main_uploaded: false,
      stage_9_started: false,
      app_bundle_reinstall_executed: false,
      data_logic_changes_made: false,
      formal_fake_financial_data_added: false,
      explicitly_not_done: [
        "Phase 8.3 manual acceptance",
        "Stage 8 whole-stage review",
        "Stage 8 GitHub main upload",
        "Stage 9 regression freeze",
        "GitHub main upload",
        "app bundle reinstall",
        "financial data mutation or synthesis",
      ],
      repo: {
        path: REPO_ROOT,
        branch: run("git", ["branch", "--show-current"], { cwd: REPO_ROOT }),
        remote: run("git", ["remote", "get-url", "origin"], { cwd: REPO_ROOT }),
        head_at_evidence_write: run("git", ["rev-parse", "HEAD"], { cwd: REPO_ROOT }),
        origin_main_at_evidence_write: run("git", ["rev-parse", "origin/main"], { cwd: REPO_ROOT }),
      },
      changed_files: changedFiles,
      generated_at: generatedAt,
    };

    writeJson("screenshot_index.json", screenshotIndex);
    writeJson("app_entry_validation.json", appEntryValidation);
    writeJson("browser_validation.json", browserValidation);
    writeJson("evidence.json", evidence);
    writeSupportFiles(changedFiles, generatedAt, publicService, browserStatus);

    console.log(JSON.stringify({
      status: browserStatus,
      app_entry: appEntryStatus,
      screenshots: screenshotIndexStatus,
      screenshot_count: screenshots.length,
      phase_dir: PHASE_DIR,
      failures: browserStatus === "pass" ? [] : browserValidation,
    }, null, 2));
    if (browserStatus !== "pass") process.exitCode = 1;
  } finally {
    if (browser) await browser.close();
    await stopTemporaryService(service);
  }
}

main().catch((error) => {
  console.error(error && error.stack ? error.stack : String(error));
  process.exit(1);
});
