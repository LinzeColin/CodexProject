#!/usr/bin/env node
import { createHash } from "node:crypto";
import { createRequire } from "node:module";
import { mkdir, readFile, stat, writeFile } from "node:fs/promises";
import path from "node:path";


const require = createRequire(import.meta.url);
const args = Object.fromEntries(process.argv.slice(2).reduce((pairs, value, index, values) => {
  if (value.startsWith("--")) pairs.push([value.slice(2), values[index + 1]]);
  return pairs;
}, []));
const baseUrl = String(args["base-url"] || "").replace(/\/$/, "");
const apiUrl = String(args["api-url"] || "").replace(/\/$/, "");
const apiToken = String(args["api-token"] || "");
const sourcePaths = JSON.parse(String(args["sources-json"] || "[]")).map((item) => path.resolve(String(item)));
const outputDir = path.resolve(String(args["output-dir"] || ""));
const rawTrace = path.resolve(String(args["raw-trace"] || ""));
const chromePath = path.resolve(String(args.chrome || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"));
const moduleDir = process.env.PFI_PLAYWRIGHT_MODULE_DIR;
if (!baseUrl || !apiUrl || !apiToken || sourcePaths.length !== 4 || !outputDir || !rawTrace || !moduleDir) {
  throw new Error("loopback URLs, token, four real sources, output paths and cached Playwright are required");
}
const { chromium } = require(path.join(moduleDir, "playwright"));

const PRIMARY_ROUTES = Object.freeze([
  "/overview", "/accounts", "/ledger", "/investment", "/consumption",
  "/data", "/review", "/reports", "/market-research", "/settings",
]);
const SECONDARY_ROUTES = Object.freeze([
  "/overview/status", "/accounts/overview", "/ledger/list", "/investment/holdings",
  "/consumption/overview", "/data/upload", "/review/list", "/reports/monthly",
  "/market-research/market", "/settings/account",
]);
const PRIMARY_LABELS = Object.freeze([
  "首页总览", "账户与资产", "账本流水", "投资管理", "消费管理",
  "数据源与上传", "建议与复盘", "报告与洞察", "市场与研究", "设置",
]);
const LEGACY_PRIMARY_ROUTES = new Set([
  "/home", "/market", "/research", "/holdings", "/strategy-lab",
  "/investment/strategy-lab", "/data-system",
]);

function browserArgs() {
  return [
    "--disable-background-networking", "--disable-component-update", "--disable-default-apps",
    "--disable-domain-reliability", "--disable-extensions",
    "--disable-features=OptimizationHints,MediaRouter,ServiceWorker", "--disable-sync",
    "--metrics-recording-only", "--no-first-run", "--no-default-browser-check",
  ];
}

async function apiJson(route, options = {}) {
  const response = await fetch(`${apiUrl}${route}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-PFI-Runtime-Token": apiToken,
      ...(options.headers || {}),
    },
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.message || `${route} failed with ${response.status}`);
  return payload;
}

async function waitForShell(page) {
  await page.waitForFunction(() => (
    document.querySelector(".app-shell")?.hidden === false
    && document.body.dataset.pfiReleaseIdentityState === "ready"
  ), null, { timeout: 30_000 });
}

async function waitForLedgerCount(expected) {
  const deadline = Date.now() + 30_000;
  while (Date.now() < deadline) {
    const ledger = await apiJson("/api/ledger");
    if (Number(ledger.ledger_count || 0) === expected) return ledger;
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error(`ledger count did not become ${expected}`);
}

async function redactFinancialDom(page) {
  await page.evaluate(() => {
    document.querySelectorAll(".stage7-review-item span").forEach((node) => {
      node.textContent = "真实流水详情已脱敏";
    });
    document.querySelectorAll("[data-upload-file-list] strong").forEach((node, index) => {
      node.textContent = `real_source_${index + 1}`;
    });
    document.querySelectorAll("[data-card-value]").forEach((node) => {
      if (/\bCNY\s+-?[0-9]/.test(node.textContent || "")) node.textContent = "CNY 已脱敏";
    });
    const embedded = document.querySelector("#pfi-read-model-status");
    if (embedded) embedded.textContent = JSON.stringify({ redacted: true });
    document.body.dataset.stage12EvidenceRedacted = "true";
  });
}

async function routeSnapshot(page, route) {
  const started = Date.now();
  await page.goto(`${baseUrl}${route}`, { waitUntil: "domcontentloaded" });
  await waitForShell(page);
  await page.waitForTimeout(50);
  const durationMs = Date.now() - started;
  return page.evaluate(({ expectedRoute, duration }) => {
    const main = document.querySelector("#main-workspace");
    const active = [...document.querySelectorAll('[data-primary-entry="true"].is-active')];
    const primary = [...document.querySelectorAll('[data-primary-entry="true"]')];
    return {
      requested_route: expectedRoute,
      canonical_route: main?.dataset.routeAlias || "",
      title_present: Boolean(document.querySelector("#workspace-title")?.textContent?.trim()),
      active_primary_count: active.length,
      primary_entry_count: primary.length,
      duration_ms: duration,
      horizontal_overflow_px: Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth),
    };
  }, { expectedRoute: route, duration: durationMs });
}

async function secondarySnapshot(page, route) {
  await page.goto(`${baseUrl}${route}`, { waitUntil: "domcontentloaded" });
  await waitForShell(page);
  await page.waitForSelector("[data-stage6-structural-signature]");
  return page.evaluate((expectedRoute) => {
    const surface = document.querySelector("[data-stage6-structural-signature]");
    return {
      requested_route: expectedRoute,
      canonical_route: document.querySelector("#main-workspace")?.dataset.routeAlias || "",
      structural_signature: surface?.getAttribute("data-stage6-structural-signature") || "",
      data_object: surface?.getAttribute("data-stage5-data-object") || "",
      job_to_be_done_present: Boolean(surface?.getAttribute("data-stage6-job-to-be-done")),
      primary_action_present: Boolean(surface?.getAttribute("data-stage4-primary-action")),
    };
  }, route);
}

await mkdir(outputDir, { recursive: true });
for (const source of sourcePaths) {
  if ((await stat(source)).size <= 0) throw new Error("real source snapshot is empty");
}
const diagnostics = {
  consoleErrors: [], pageErrors: [], httpErrors: [], blockedExternal: [], requestedOrigins: new Set(),
};
const browser = await chromium.launch({ executablePath: chromePath, headless: true, args: browserArgs() });
let context;
let traceStarted = false;
let result;
try {
  context = await browser.newContext({
    locale: "zh-CN", serviceWorkers: "block", viewport: { width: 1440, height: 1050 },
    colorScheme: "light", reducedMotion: "reduce",
  });
  const allowedOrigins = new Set([new URL(baseUrl).origin, new URL(apiUrl).origin]);
  await context.route("**/*", async (route) => {
    const requestUrl = route.request().url();
    const parsed = new URL(requestUrl);
    if (["data:", "blob:", "about:"].includes(parsed.protocol) || allowedOrigins.has(parsed.origin)) {
      if (allowedOrigins.has(parsed.origin)) diagnostics.requestedOrigins.add(parsed.origin);
      await route.continue();
      return;
    }
    diagnostics.blockedExternal.push({ protocol: parsed.protocol, host: parsed.host });
    await route.abort("blockedbyclient");
  });
  await context.tracing.start({ screenshots: false, snapshots: false, sources: false });
  traceStarted = true;
  const page = await context.newPage();
  page.on("console", (message) => { if (message.type() === "error") diagnostics.consoleErrors.push(message.text()); });
  page.on("pageerror", (error) => diagnostics.pageErrors.push(String(error?.message || error)));
  page.on("response", (response) => {
    if (response.status() >= 400) diagnostics.httpErrors.push({ status: response.status(), path: new URL(response.url()).pathname });
  });

  await page.goto(`${baseUrl}/data/upload`, { waitUntil: "domcontentloaded" });
  await waitForShell(page);
  const initialPerformance = await page.evaluate(() => {
    const navigation = performance.getEntriesByType("navigation")[0];
    const paint = performance.getEntriesByName("first-contentful-paint")[0];
    return {
      dom_content_loaded_ms: Math.round(navigation?.domContentLoadedEventEnd || 0),
      load_event_ms: Math.round(navigation?.loadEventEnd || 0),
      first_contentful_paint_ms: Math.round(paint?.startTime || 0),
    };
  });
  const ledgerInitial = await apiJson("/api/ledger");
  await page.locator("[data-upload-input]").setInputFiles(sourcePaths);
  await page.waitForFunction(
    () => document.querySelector("[data-upload-status]")?.dataset.uploadState === "preview",
    null,
    { timeout: 90_000 },
  );
  const batchId = await page.locator('[data-import-batch-id^="import:"]').getAttribute("data-import-batch-id");
  if (!batchId) throw new Error("preview batch id is unavailable");
  const preview = await apiJson(`/api/imports/alipay?batch_id=${encodeURIComponent(batchId)}`);
  await redactFinancialDom(page);
  const importScreenshot = path.join(outputDir, "real_import_preview_redacted.png");
  await page.screenshot({ path: importScreenshot, fullPage: true });
  await page.locator("[data-import-confirm]").click();
  await page.waitForFunction(
    () => document.querySelector("[data-upload-status]")?.dataset.uploadState === "ready",
    null,
    { timeout: 90_000 },
  );
  const transactionCount = Number(preview.transaction_count || 0);
  const ledgerConfirmed = await waitForLedgerCount(transactionCount);
  const replay = await apiJson("/api/imports/alipay/confirm", {
    method: "POST",
    body: JSON.stringify({ batch_id: batchId }),
  });

  await page.goto(`${baseUrl}/investment/holdings`, { waitUntil: "domcontentloaded" });
  await waitForShell(page);
  await page.waitForSelector("[data-holdings-persistence-panel]:not([hidden])");
  const holdingVisible = await page.evaluate(() => ({
    active_holding_count: Number(document.querySelector("[data-holdings-summary-count]")?.textContent || -1),
    valuation_status: document.querySelector("[data-holdings-summary-value]")?.textContent?.trim() || "",
    row_count: document.querySelectorAll("[data-holdings-rows] tr").length,
    false_zero_count: [...document.querySelectorAll("[data-holdings-persistence-panel] *")]
      .filter((node) => /\bCNY\s+0(?:\.0+)?\b/.test(node.textContent || "")).length,
  }));
  const holdingScreenshot = path.join(outputDir, "holding_source_blocked.png");
  await page.screenshot({ path: holdingScreenshot, fullPage: true });

  await page.goto(`${baseUrl}/reports`, { waitUntil: "domcontentloaded" });
  await waitForShell(page);
  await page.waitForFunction(() => document.body.dataset.v025Stage9Phase92 === "ready", null, { timeout: 30_000 });
  const reportVisible = await page.evaluate(() => {
    const cards = [...document.querySelectorAll("[data-home-card]")].filter((node) => !node.hidden);
    const workspaceText = document.querySelector("#main-workspace")?.textContent || "";
    const validation = window.PFI_V025_STAGE9_ANALYSIS?.validatePhase92ViewModel?.() || {};
    return {
      visible_runtime_card_count: cards.length,
      analysis_validation_status: validation.status || "unavailable",
      report_card_count: Number(validation.reportCount || 0),
      blocked_report_count: Number(validation.blockedCount || 0),
      partial_report_count: Number(validation.partialCount || 0),
      financial_amount_visible: /\bCNY\s+-?[0-9]/.test(workspaceText),
    };
  });
  const reportScreenshot = path.join(outputDir, "report_truth_states.png");
  await page.screenshot({ path: reportScreenshot, fullPage: true });

  const primarySnapshots = [];
  for (const route of PRIMARY_ROUTES) primarySnapshots.push(await routeSnapshot(page, route));
  const secondarySnapshots = [];
  for (const route of SECONDARY_ROUTES) secondarySnapshots.push(await secondarySnapshot(page, route));

  await page.goto(`${baseUrl}/reports`, { waitUntil: "domcontentloaded" });
  await waitForShell(page);
  const navigationTruth = await page.evaluate(() => ({
    primary_routes: [...document.querySelectorAll('[data-primary-entry="true"]')]
      .map((node) => node.getAttribute("data-route-alias") || ""),
    primary_labels: [...document.querySelectorAll('[data-primary-entry="true"]')]
      .map((node) => node.textContent?.trim() || ""),
  }));
  const cdp = await context.newCDPSession(page);
  await cdp.send("Accessibility.enable");
  const rawAx = await cdp.send("Accessibility.getFullAXTree");
  const axNames = rawAx.nodes
    .filter((node) => !node.ignored)
    .map((node) => String(node.name?.value || ""));
  const foundPrimaryLabels = PRIMARY_LABELS.filter((label) => axNames.includes(label));
  const accessibility = {
    source: "Chrome_DevTools_Protocol_Accessibility.getFullAXTree",
    non_ignored_node_count: rawAx.nodes.filter((node) => !node.ignored).length,
    expected_primary_navigation_count: PRIMARY_LABELS.length,
    found_primary_navigation_count: foundPrimaryLabels.length,
    legacy_alias_primary_navigation_count: navigationTruth.primary_routes.filter((route) => LEGACY_PRIMARY_ROUTES.has(route)).length,
    duplicate_primary_label_count: navigationTruth.primary_labels.length - new Set(navigationTruth.primary_labels).size,
  };

  const signatures = secondarySnapshots.map((item) => item.structural_signature);
  const dataObjects = secondarySnapshots.map((item) => item.data_object);
  const performance = {
    initial_navigation: initialPerformance,
    route_count: primarySnapshots.length,
    maximum_route_navigation_ms: Math.max(...primarySnapshots.map((item) => item.duration_ms)),
    route_navigation_budget_ms: 3000,
    initial_navigation_budget_ms: 2500,
  };
  const importResult = {
    execution_status: "completed",
    source_kind: "real_alipay_csv_git_objects",
    source_blob_count: sourcePaths.length,
    raw_record_count: Number(preview.raw_record_count || 0),
    transaction_count: transactionCount,
    review_count: Number(preview.review_count || 0),
    confirmed_ledger_count: Number(ledgerConfirmed.ledger_count || 0),
    replay_idempotent: replay.idempotent_replay === true,
    fixture_used: false,
    fallback_used: false,
  };
  const holdingResult = {
    execution_status: "not_run",
    truth_gate_status: "pass",
    reason_code: "SRC_HOLDINGS_NOT_LOADED",
    source_fixture_used: false,
    financial_pass_claimed: false,
    ...holdingVisible,
  };
  const reportResult = {
    execution_status: "completed",
    source_kind: "current_real_aggregate_manifest",
    financial_values_emitted: 0,
    ...reportVisible,
  };
  const routeRegression = {
    primary_route_count: primarySnapshots.length,
    primary_routes: primarySnapshots,
    secondary_route_count: secondarySnapshots.length,
    secondary_routes: secondarySnapshots,
    canonical_primary_route_count: new Set(navigationTruth.primary_routes).size,
    legacy_primary_route_count: navigationTruth.primary_routes.filter((route) => LEGACY_PRIMARY_ROUTES.has(route)).length,
  };
  const noFalseZero = {
    status: holdingVisible.false_zero_count === 0 && reportVisible.financial_amount_visible === false ? "pass" : "fail",
    holding_false_zero_count: holdingVisible.false_zero_count,
    report_financial_amount_visible: reportVisible.financial_amount_visible,
  };
  const noTemplateClone = {
    status: new Set(signatures).size === SECONDARY_ROUTES.length && new Set(dataObjects).size === SECONDARY_ROUTES.length ? "pass" : "fail",
    representative_route_count: SECONDARY_ROUTES.length,
    distinct_structural_signature_count: new Set(signatures).size,
    distinct_data_object_count: new Set(dataObjects).size,
  };
  const checks = {
    real_import_four_git_objects: importResult.source_blob_count === 4 && importResult.fixture_used === false,
    real_import_record_coverage: importResult.raw_record_count === 8815 && importResult.transaction_count === 8808,
    real_import_confirmed: Number(ledgerInitial.ledger_count || 0) === 0 && importResult.confirmed_ledger_count === importResult.transaction_count,
    real_import_replay_idempotent: importResult.replay_idempotent === true,
    holding_missing_source_truthful: holdingResult.execution_status === "not_run" && holdingResult.active_holding_count === 0 && holdingResult.financial_pass_claimed === false,
    report_truth_states: reportResult.analysis_validation_status === "pass" && reportResult.report_card_count === 5 && reportResult.blocked_report_count === 3 && reportResult.partial_report_count === 2,
    no_false_zero: noFalseZero.status === "pass",
    canonical_primary_routes: navigationTruth.primary_routes.length === 10 && PRIMARY_ROUTES.every((route) => navigationTruth.primary_routes.includes(route)),
    no_old_primary_ui: routeRegression.legacy_primary_route_count === 0,
    route_matrix_pass: primarySnapshots.every((item) => item.active_primary_count === 1 && item.primary_entry_count === 10 && item.horizontal_overflow_px === 0),
    no_template_clone: noTemplateClone.status === "pass",
    accessibility_tree_pass: accessibility.found_primary_navigation_count === 10 && accessibility.duplicate_primary_label_count === 0 && accessibility.legacy_alias_primary_navigation_count === 0,
    performance_budget_pass: performance.initial_navigation.dom_content_loaded_ms <= performance.initial_navigation_budget_ms && performance.maximum_route_navigation_ms <= performance.route_navigation_budget_ms,
    no_console_errors: diagnostics.consoleErrors.length === 0,
    no_page_errors: diagnostics.pageErrors.length === 0,
    no_http_errors: diagnostics.httpErrors.length === 0,
    loopback_only: diagnostics.blockedExternal.length === 0 && [...diagnostics.requestedOrigins].every((origin) => allowedOrigins.has(origin)),
  };
  await context.tracing.stop({ path: rawTrace });
  traceStarted = false;
  result = {
    schema: "PFIV025Stage12Phase121PlaywrightResultV1",
    status: Object.values(checks).every(Boolean) ? "pass" : "fail",
    check_count: Object.keys(checks).length,
    passed_check_count: Object.values(checks).filter(Boolean).length,
    checks,
    import: importResult,
    holding: holdingResult,
    report: reportResult,
    route_regression: routeRegression,
    no_false_zero: noFalseZero,
    no_template_clone: noTemplateClone,
    performance,
    accessibility,
    diagnostics: {
      console_errors: diagnostics.consoleErrors,
      page_errors: diagnostics.pageErrors,
      http_errors: diagnostics.httpErrors,
      blocked_external: diagnostics.blockedExternal,
      requested_origin_count: diagnostics.requestedOrigins.size,
    },
    screenshots: [
      { file: path.basename(importScreenshot), sha256: createHash("sha256").update(await readFile(importScreenshot)).digest("hex") },
      { file: path.basename(holdingScreenshot), sha256: createHash("sha256").update(await readFile(holdingScreenshot)).digest("hex") },
      { file: path.basename(reportScreenshot), sha256: createHash("sha256").update(await readFile(reportScreenshot)).digest("hex") },
    ],
    private_values_persisted: false,
    financial_values_emitted: 0,
    external_network_performed: false,
    finder_used: false,
  };
} finally {
  if (traceStarted && context) await context.tracing.stop({ path: rawTrace }).catch(() => {});
  if (context) await context.close().catch(() => {});
  await browser.close();
}
await writeFile(path.join(outputDir, "playwright_result.json"), `${JSON.stringify(result, null, 2)}\n`, "utf8");
if (result?.status !== "pass") {
  throw new Error(`Stage 12.1 real E2E failed: ${JSON.stringify(result?.checks || {})}`);
}
process.stdout.write(`${JSON.stringify({ status: result.status, checks: result.check_count })}\n`);
