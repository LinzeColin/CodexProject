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
const REPO_ROOT = path.resolve(ROOT, "..");
const WEB_ROOT = path.join(ROOT, "web");
const PHASE_DIR = path.join(ROOT, "reports", "pfi_v024", "stage_8", "phase_8_1");
const READ_MODEL_PATH = path.join(ROOT, "reports", "pfi_v024", "stage_4", "phase_4_2", "read_model_status.json");
const REPORT_SCHEMA_PATH = path.join(ROOT, "reports", "pfi_v024", "stage_7", "phase_7_1", "report_schema.json");
const STAGE7_UPLOAD_PATH = path.join(ROOT, "reports", "pfi_v024", "stage_7", "github_main_upload", "evidence.json");
const PLAYWRIGHT_PACKAGE_PATH = process.env.PLAYWRIGHT_PACKAGE_PATH || "";
const EXPECTED_PRIMARY_LABELS = Object.freeze([
  "首页总览",
  "账户与资产",
  "账本流水",
  "投资管理",
  "消费管理",
  "数据源与上传",
  "建议与复盘",
  "报告与洞察",
  "市场与研究",
  "设置",
]);
const BUNDLE_FILES = Object.freeze([
  "web/index.html",
  "web/styles/tokens.css",
  "web/app/version.js",
  "web/app/entry_audit.js",
  "web/app/navigation.js",
  "web/app/routes.js",
  "web/app/data_state.js",
  "web/app/pages/stage4Subpages.js",
  "web/app/pages/stage5Subpages.js",
  "web/app/ux_state.js",
  "web/app/pages/home.js",
  "web/app/pages/reports.js",
  "web/app/feedback.js",
  "web/app/pages/settings.js",
  "web/app/shell.js",
]);
const serverNotFoundPaths = [];

function ensureDirs() {
  fs.mkdirSync(PHASE_DIR, { recursive: true });
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf-8"));
}

function writeJson(fileName, payload) {
  fs.writeFileSync(path.join(PHASE_DIR, fileName), `${JSON.stringify(payload, null, 2)}\n`);
}

function relativePath(filePath) {
  return path.relative(REPO_ROOT, filePath).split(path.sep).join("/");
}

function fileSha256(filePath) {
  return crypto.createHash("sha256").update(fs.readFileSync(filePath)).digest("hex");
}

function buildBundleMetadata() {
  const files = [];
  const bundleDigest = crypto.createHash("sha256");
  for (const relative of BUNDLE_FILES) {
    const absolute = path.join(ROOT, relative);
    const sha256 = fileSha256(absolute);
    files.push({ path: `PFI/${relative}`, sha256, bytes: fs.statSync(absolute).size });
    bundleDigest.update(relative);
    bundleDigest.update(Buffer.from([0]));
    bundleDigest.update(sha256);
    bundleDigest.update(Buffer.from([0]));
  }
  const byPath = Object.fromEntries(files.map((item) => [item.path, item.sha256]));
  return {
    schema: "PFIV024Stage8Phase81RuntimeMetadataV1",
    targetVersion: "v0.2.4",
    sourcePackageVersion: "v0.2.3-repair",
    repairLabel: "PFI v0.2.3 Repair",
    buildId: "pfi-v024-stage2-phase22",
    bundleVersion: "20260630.2",
    uiContractVersion: "PFI-V024-STAGE2-ENTRY-CONSISTENCY",
    stage: "Stage 8",
    phase: "8.1",
    projectRoot: ROOT,
    webBundleHash: bundleDigest.digest("hex"),
    webIndexSha256: byPath["PFI/web/index.html"],
    tokensCssSha256: byPath["PFI/web/styles/tokens.css"],
    versionJsSha256: byPath["PFI/web/app/version.js"],
    entryAuditJsSha256: byPath["PFI/web/app/entry_audit.js"],
    routesJsSha256: byPath["PFI/web/app/routes.js"],
    shellJsSha256: byPath["PFI/web/app/shell.js"],
    frontendBundleFiles: BUNDLE_FILES,
  };
}

function escapeScriptJson(payload) {
  return JSON.stringify(payload).replace(/<\//g, "<\\/");
}

function replaceJsonScript(html, id, payload) {
  const next = `<script type="application/json" id="${id}">${escapeScriptJson(payload)}</script>`;
  const pattern = new RegExp(`<script\\b[^>]*id=["']${id}["'][^>]*>[\\s\\S]*?<\\/script>`);
  if (pattern.test(html)) return html.replace(pattern, next);
  return html.replace("</body>", `${next}\n</body>`);
}

function buildIndexHtml({ runtimeMetadata, readModelStatus, reportSchema }) {
  let html = fs.readFileSync(path.join(WEB_ROOT, "index.html"), "utf-8");
  html = replaceJsonScript(html, "pfi-runtime-config", {
    ...runtimeMetadata,
    apiBaseUrl: "http://127.0.0.1:8766",
    readModelStatusApi: false,
  });
  html = replaceJsonScript(html, "pfi-read-model-status", readModelStatus);
  html = replaceJsonScript(html, "pfi-stage7-report-schema", reportSchema);
  return html;
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

function startStaticServer(indexHtml, readModelStatus) {
  const apiPayload = JSON.stringify(readModelStatus);
  const server = http.createServer((request, response) => {
    try {
      const requestUrl = new URL(request.url || "/", "http://127.0.0.1");
      if (requestUrl.pathname === "/favicon.ico") {
        response.writeHead(204);
        response.end();
        return;
      }
      if (requestUrl.pathname === "/api/read-model-status") {
        response.writeHead(200, { "Content-Type": "application/json; charset=utf-8" });
        response.end(apiPayload);
        return;
      }
      if (requestUrl.pathname === "/api/trends" || requestUrl.pathname === "/api/read-model") {
        response.writeHead(200, { "Content-Type": "application/json; charset=utf-8" });
        response.end(JSON.stringify({ status: "not_mounted_static_phase81", trends: {}, readModel: {} }));
        return;
      }
      const requestPath = decodeURIComponent(requestUrl.pathname === "/" ? "/index.html" : requestUrl.pathname);
      if (requestPath === "/index.html") {
        response.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
        response.end(indexHtml);
        return;
      }
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
    return document.querySelector(".app-shell")?.dataset.state === "ready"
      && Boolean(window.PFI_READ_STAGE2_ENTRY_AUDIT)
      && Boolean(window.PFI_V024_STAGE4_DATA_STATE)
      && Boolean(window.PFI_V024_STAGE5_PAGES)
      && Boolean(window.PFI_V024_STAGE7_REPORTS);
  });
}

async function activeWorkspace(page) {
  return page.locator("#main-workspace").evaluate((node) => node.dataset.activeWorkspace || "");
}

async function activeRoute(page) {
  return page.locator("#main-workspace").evaluate((node) => node.dataset.routeAlias || "");
}

async function clickPrimaryRoute(page, routeAlias, expectedWorkspace) {
  await page.locator(`[data-primary-entry="true"][data-route-alias="${routeAlias}"]`).click();
  await page.waitForFunction((workspace) => {
    return document.querySelector("#main-workspace")?.dataset.activeWorkspace === workspace;
  }, expectedWorkspace);
  const workspace = await activeWorkspace(page);
  const route = await activeRoute(page);
  if (workspace !== expectedWorkspace || route !== routeAlias) {
    throw new Error(`primary route ${routeAlias} resolved workspace=${workspace} route=${route}`);
  }
}

async function navigateHashRoute(page, baseUrl, routeAlias, expectedWorkspace) {
  await page.goto(`${baseUrl}/index.html#${routeAlias}`, { waitUntil: "networkidle" });
  await waitForReady(page);
  await page.waitForFunction((workspace) => {
    return document.querySelector("#main-workspace")?.dataset.activeWorkspace === workspace;
  }, expectedWorkspace);
  const workspace = await activeWorkspace(page);
  const route = await activeRoute(page);
  if (workspace !== expectedWorkspace || route !== routeAlias) {
    throw new Error(`hash route ${routeAlias} resolved workspace=${workspace} route=${route}`);
  }
}

async function buildRouteClickValidation(page, baseUrl) {
  const primaryEntries = await page.$$eval('[data-primary-entry="true"]', (nodes) => nodes.map((node) => ({
    label: node.textContent.trim(),
    routeAlias: node.getAttribute("data-route-alias") || "",
    workspace: node.getAttribute("data-workspace") || "",
  })));
  if (primaryEntries.length !== 10) throw new Error(`primary entry count ${primaryEntries.length}`);
  for (const entry of primaryEntries) {
    await clickPrimaryRoute(page, entry.routeAlias, entry.workspace);
  }

  const coreSecondaryRoutes = await page.evaluate(() => {
    const catalog = window.PFI_V024_STAGE5_PAGES.buildV024Stage5Phase52Catalog();
    return Object.entries(catalog).map(([workspace, pages]) => {
      const page = pages[1] || pages[0];
      return {
        workspace,
        routeAlias: page.routeAlias,
        title: page.title,
      };
    });
  });
  for (const route of coreSecondaryRoutes) {
    await navigateHashRoute(page, baseUrl, route.routeAlias, route.workspace);
  }

  await navigateHashRoute(page, baseUrl, primaryEntries[1].routeAlias, primaryEntries[1].workspace);
  await navigateHashRoute(page, baseUrl, primaryEntries[3].routeAlias, primaryEntries[3].workspace);
  await page.goBack();
  await page.waitForFunction((workspace) => {
    return document.querySelector("#main-workspace")?.dataset.activeWorkspace === workspace;
  }, primaryEntries[1].workspace);
  const backRoute = await activeRoute(page);
  await page.goForward();
  await page.waitForFunction((workspace) => {
    return document.querySelector("#main-workspace")?.dataset.activeWorkspace === workspace;
  }, primaryEntries[3].workspace);
  const forwardRoute = await activeRoute(page);
  const historyBackForwardPassed = backRoute === primaryEntries[1].routeAlias && forwardRoute === primaryEntries[3].routeAlias;

  const primaryLabels = primaryEntries.map((entry) => entry.label);
  const allPrimaryRoutesClicked = JSON.stringify(primaryLabels) === JSON.stringify(EXPECTED_PRIMARY_LABELS);
  const allCoreSecondaryRoutesClicked = coreSecondaryRoutes.length >= 10;
  return {
    schema: "PFIV024Stage8Phase81RouteClickValidationV1",
    target_version: "v0.2.4",
    source_package_version: "v0.2.3-repair",
    stage: "Stage 8",
    phase_id: "8.1",
    status: allPrimaryRoutesClicked && allCoreSecondaryRoutesClicked && historyBackForwardPassed ? "pass" : "fail",
    primary_entry_count: primaryEntries.length,
    primary_labels: primaryLabels,
    primary_routes: primaryEntries,
    core_secondary_route_count: coreSecondaryRoutes.length,
    core_secondary_routes: coreSecondaryRoutes,
    all_primary_routes_clicked: allPrimaryRoutesClicked,
    all_core_secondary_routes_clicked: allCoreSecondaryRoutesClicked,
    history_back_forward_passed: historyBackForwardPassed,
  };
}

async function buildEntryVersionValidation(page) {
  const audit = await page.evaluate(() => window.PFI_READ_STAGE2_ENTRY_AUDIT());
  const webBundleHashPresent = Boolean(audit.webBundleHash && String(audit.webBundleHash).length >= 32);
  const status = audit.targetVersion === "v0.2.4"
    && audit.sourcePackageVersion === "v0.2.3-repair"
    && audit.repairLabel === "PFI v0.2.3 Repair"
    && audit.buildId === "pfi-v024-stage2-phase22"
    && audit.uiContractVersion === "PFI-V024-STAGE2-ENTRY-CONSISTENCY"
    && webBundleHashPresent
    ? "pass"
    : "fail";
  return {
    schema: "PFIV024Stage8Phase81EntryVersionValidationV1",
    target_version: audit.targetVersion,
    source_package_version: audit.sourcePackageVersion,
    repair_label: audit.repairLabel,
    build_id: audit.buildId,
    bundle_version: audit.bundleVersion,
    ui_contract_version: audit.uiContractVersion,
    web_bundle_hash: audit.webBundleHash,
    web_bundle_hash_present: webBundleHashPresent,
    project_root: audit.projectRoot,
    entry_source: audit.entrySource,
    status,
  };
}

async function buildDataStateValidation(page) {
  return page.evaluate(() => {
    const payload = JSON.parse(document.getElementById("pfi-read-model-status")?.textContent || "{}");
    const api = window.PFI_V024_STAGE4_DATA_STATE;
    const normalized = api.normalizeReadModelStatus(payload);
    const metrics = normalized.core_metric_states || [];
    const blocked = metrics.filter((metric) => !["ready", "confirmed_zero"].includes(metric.status));
    const rendered = metrics.map((metric) => ({
      metric_id: metric.metric_id,
      status: metric.status,
      display: api.renderMetricValueZh(metric),
    }));
    const text = JSON.stringify(rendered);
    const falseZero = blocked.some((metric) => api.renderMetricValueZh(metric).includes("CNY 0.00"));
    const source = normalized.source || {};
    const status = source.status === "ready"
      && Number(source.record_count || 0) === 8815
      && Number(source.raw_file_count || 0) === 4
      && !falseZero
      ? "pass"
      : "fail";
    return {
      schema: "PFIV024Stage8Phase81DataStateValidationV1",
      target_version: "v0.2.4",
      source_package_version: "v0.2.3-repair",
      stage: "Stage 8",
      phase_id: "8.1",
      status,
      read_model_hash: normalized.read_model_hash,
      source_status: source.status || null,
      source_record_count: Number(source.record_count || 0),
      source_raw_file_count: Number(source.raw_file_count || 0),
      source_date_range: source.date_range || { start: null, end: null },
      source_as_of: source.as_of || null,
      blocked_metric_ids: blocked.map((metric) => metric.metric_id),
      false_financial_zero_visible: falseZero,
      rendered_text_contains_cny_zero: text.includes("CNY 0.00"),
      rendered_metrics: rendered,
    };
  });
}

async function buildReportCenterValidation(page) {
  return page.evaluate(() => {
    const reportPack = JSON.parse(document.getElementById("pfi-stage7-report-schema")?.textContent || "{}");
    const api = window.PFI_V024_STAGE7_REPORTS;
    const view = api.buildV024Stage7Phase72ReportCenterViewModel(reportPack);
    const pageValidation = api.validateV024Stage7Phase72ReportCenterViewModel(view);
    const acceptance = api.validateV024Stage7Phase73Acceptance(view);
    const blockedCards = view.report_cards.filter((card) => card.status === "blocked");
    const fullFinancialConclusionWhenBlocked = blockedCards.some((card) => String(card.conclusion_zh || "").includes("完整财务结论"));
    return {
      schema: "PFIV024Stage8Phase81ReportCenterValidationV1",
      target_version: "v0.2.4",
      source_package_version: "v0.2.3-repair",
      stage: "Stage 8",
      phase_id: "8.1",
      status: pageValidation.status === "pass" && acceptance.status === "pass" && !fullFinancialConclusionWhenBlocked ? "pass" : "fail",
      report_count: view.report_count,
      visible_report_ids: pageValidation.visible_report_ids,
      formula_visible: pageValidation.formula_visible,
      parameters_and_sample_visible: pageValidation.parameters_and_sample_visible,
      data_range_visible: pageValidation.data_range_visible,
      confidence_visible: pageValidation.confidence_visible,
      gaps_and_review_visible: pageValidation.gaps_and_review_visible,
      data_quality_report_generated: acceptance.data_quality_report_generated,
      full_financial_conclusion_when_blocked: fullFinancialConclusionWhenBlocked,
      blocked_count: view.blocked_count,
      partial_count: view.partial_count,
    };
  });
}

function buildEvidence({ route, entry, dataState, reports, browserValidation, generatedAt }) {
  const stage7Upload = readJson(STAGE7_UPLOAD_PATH);
  const changedFiles = [
    "PFI/CHANGELOG.md",
    "PFI/HANDOFF.md",
    "PFI/README.md",
    "PFI/docs/pfi_v024/RUN_CONTRACT.md",
    "PFI/docs/pfi_v024/STAGE8_E2E_ACCEPTANCE.md",
    "PFI/reports/pfi_v024/stage_8/phase_8_1/browser_validation.json",
    "PFI/reports/pfi_v024/stage_8/phase_8_1/changed_files.txt",
    "PFI/reports/pfi_v024/stage_8/phase_8_1/data_state_validation.json",
    "PFI/reports/pfi_v024/stage_8/phase_8_1/entry_version_validation.json",
    "PFI/reports/pfi_v024/stage_8/phase_8_1/evidence.json",
    "PFI/reports/pfi_v024/stage_8/phase_8_1/report_center_validation.json",
    "PFI/reports/pfi_v024/stage_8/phase_8_1/risk_and_rollback.md",
    "PFI/reports/pfi_v024/stage_8/phase_8_1/route_click_validation.json",
    "PFI/reports/pfi_v024/stage_8/phase_8_1/terminal.log",
    "PFI/scripts/validate_v024_stage8_phase81_e2e_auto.js",
    "PFI/src/pfi_v02/stage_v024_stage8_e2e_acceptance.py",
    "PFI/tests/test_v024_stage8_phase81_e2e_auto_acceptance.py",
    "PFI/功能清单.md",
    "PFI/开发记录.md",
    "PFI/模型参数文件.md",
  ];
  return {
    schema: "PFIV024Stage8Phase81EvidenceV1",
    version: "v0.2.3-repair",
    target_version: "v0.2.4",
    source_package_version: "v0.2.3-repair",
    stage: "Stage 8",
    stage_name: "端到端浏览器与 app 验收",
    phase_id: "8.1",
    phase_name: "自动验收",
    status: browserValidation.status === "pass" ? "candidate_pass" : "fail",
    current_phase_only: true,
    task_ids: ["T8.1.1", "T8.1.2", "T8.1.3", "T8.1.4"],
    stage_7_github_main_uploaded_required: true,
    stage_7_github_main_uploaded_verified: stage7Upload.status === "pass" && stage7Upload.stage_7_complete === true,
    route_click_test_passed: route.status === "pass",
    entry_version_test_passed: entry.status === "pass",
    data_state_test_passed: dataState.status === "pass",
    report_center_test_passed: reports.status === "pass",
    browser_validation: relativePath(path.join(PHASE_DIR, "browser_validation.json")),
    route_click_validation: relativePath(path.join(PHASE_DIR, "route_click_validation.json")),
    entry_version_validation: relativePath(path.join(PHASE_DIR, "entry_version_validation.json")),
    data_state_validation: relativePath(path.join(PHASE_DIR, "data_state_validation.json")),
    report_center_validation: relativePath(path.join(PHASE_DIR, "report_center_validation.json")),
    phase_8_2_started: false,
    phase_8_3_started: false,
    stage_8_whole_review_complete: false,
    github_main_uploaded: false,
    stage_9_started: false,
    app_bundle_reinstall_executed: false,
    data_logic_changes_made: false,
    formal_fake_financial_data_added: false,
    explicitly_not_done: [
      "Phase 8.2 screenshot acceptance",
      "Phase 8.3 manual acceptance",
      "Stage 8 whole-stage review",
      "Stage 8 GitHub main upload",
      "Stage 9 regression freeze",
      "GitHub main upload",
      "app bundle reinstall",
      "financial data mutation or synthesis",
    ],
    changed_files: changedFiles,
    generated_at: generatedAt,
  };
}

function writeSupportFiles(changedFiles, generatedAt) {
  fs.writeFileSync(path.join(PHASE_DIR, "changed_files.txt"), `${changedFiles.join("\n")}\n`);
  fs.writeFileSync(path.join(PHASE_DIR, "risk_and_rollback.md"), [
    "# Stage 8 Phase 8.1 Risk and Rollback",
    "",
    "## Risk",
    "",
    "- 本轮只执行 Stage 8 Phase 8.1 自动验收。",
    "- 本轮不执行 Phase 8.2 截图验收、Phase 8.3 人工验收、Stage 8 whole-stage review、Stage 9 或 GitHub main upload。",
    "- 本轮不重装 app bundle，不写入或改写真实财务数据。",
    "",
    "## Rollback",
    "",
    "如自动验收失败，保留 JSON 证据并回到对应失败 Stage 修复；不要用 Stage 8 文档覆盖失败。",
    "本轮变更可通过回退 Stage 8.1 合同、脚本、测试、文档和 evidence 文件撤销。",
    "",
  ].join("\n"));
  fs.writeFileSync(path.join(PHASE_DIR, "terminal.log"), [
    "Stage 8 Phase 8.1 automated acceptance validation log",
    "",
    "RED:",
    "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage8_phase81_e2e_auto_acceptance.py -q",
    "4 failed: missing stage_v024_stage8_e2e_acceptance module, STAGE8_E2E_ACCEPTANCE.md, and phase_8_1 evidence pack",
    "",
    "Generation:",
    "node PFI/scripts/validate_v024_stage8_phase81_e2e_auto.js",
    `generated_at ${generatedAt}`,
    "",
    "Final validation commands are recorded in the run terminal after the GREEN pass.",
    "",
  ].join("\n"));
}

async function main() {
  ensureDirs();
  const generatedAt = new Date().toISOString();
  const runtimeMetadata = buildBundleMetadata();
  const readModelStatus = readJson(READ_MODEL_PATH);
  const reportSchema = readJson(REPORT_SCHEMA_PATH);
  const indexHtml = buildIndexHtml({ runtimeMetadata, readModelStatus, reportSchema });
  const { server, baseUrl } = await startStaticServer(indexHtml, readModelStatus);
  const consoleErrors = [];
  const pageErrors = [];
  const httpErrors = [];
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

    await page.goto(`${baseUrl}/index.html`, { waitUntil: "networkidle" });
    await waitForReady(page);

    const route = await buildRouteClickValidation(page, baseUrl);
    const entry = await buildEntryVersionValidation(page);
    const dataState = await buildDataStateValidation(page);
    const reports = await buildReportCenterValidation(page);
    const browserStatus = (
      route.status === "pass"
      && entry.status === "pass"
      && dataState.status === "pass"
      && reports.status === "pass"
      && consoleErrors.length === 0
      && pageErrors.length === 0
      && httpErrors.length === 0
      && serverNotFoundPaths.length === 0
    ) ? "pass" : "fail";
    const browserValidation = {
      schema: "PFIV024Stage8Phase81BrowserValidationV1",
      target_version: "v0.2.4",
      source_package_version: "v0.2.3-repair",
      stage: "Stage 8",
      phase_id: "8.1",
      phase_name: "自动验收",
      status: browserStatus,
      automated_only: true,
      source: `${baseUrl}/index.html`,
      playwright_package_path: PLAYWRIGHT_PACKAGE_PATH,
      route_click_test_passed: route.status === "pass",
      entry_version_test_passed: entry.status === "pass",
      data_state_test_passed: dataState.status === "pass",
      report_center_test_passed: reports.status === "pass",
      history_back_forward_passed: route.history_back_forward_passed,
      console_errors: consoleErrors,
      page_errors: pageErrors,
      http_errors: httpErrors,
      server_not_found_paths: serverNotFoundPaths,
      generated_at: generatedAt,
      validation_hash: crypto.createHash("sha256").update(JSON.stringify({
        route,
        entry,
        dataState,
        reports,
        runtimeMetadataHash: runtimeMetadata.webBundleHash,
      })).digest("hex"),
    };
    const evidence = buildEvidence({ route, entry, dataState, reports, browserValidation, generatedAt });

    writeJson("route_click_validation.json", route);
    writeJson("entry_version_validation.json", entry);
    writeJson("data_state_validation.json", dataState);
    writeJson("report_center_validation.json", reports);
    writeJson("browser_validation.json", browserValidation);
    writeJson("evidence.json", evidence);
    writeSupportFiles(evidence.changed_files, generatedAt);

    console.log(JSON.stringify({
      status: browserValidation.status,
      route_click: route.status,
      entry_version: entry.status,
      data_state: dataState.status,
      report_center: reports.status,
      phase_dir: PHASE_DIR,
      failures: browserValidation.status === "pass" ? [] : browserValidation,
    }, null, 2));
    if (browserValidation.status !== "pass") process.exitCode = 1;
  } finally {
    if (browser) await browser.close();
    await new Promise((resolve) => server.close(resolve));
  }
}

main().catch((error) => {
  console.error(error && error.stack ? error.stack : String(error));
  process.exit(1);
});
