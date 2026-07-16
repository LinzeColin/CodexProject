#!/usr/bin/env node
import { createRequire } from "node:module";
import { writeFile } from "node:fs/promises";
import path from "node:path";


const require = createRequire(import.meta.url);
const args = Object.fromEntries(process.argv.slice(2).reduce((pairs, value, index, values) => {
  if (value.startsWith("--")) pairs.push([value.slice(2), values[index + 1]]);
  return pairs;
}, []));
const baseUrl = String(args["base-url"] || "").replace(/\/$/, "");
const apiUrl = String(args["api-url"] || "").replace(/\/$/, "");
const apiToken = String(args["api-token"] || "");
const outputDir = path.resolve(String(args["output-dir"] || ""));
const rawTrace = path.resolve(String(args["raw-trace"] || ""));
const chromePath = path.resolve(String(args.chrome || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"));
const moduleDir = process.env.PFI_PLAYWRIGHT_MODULE_DIR;
if (!baseUrl || !apiUrl || !apiToken || !outputDir || !rawTrace || !moduleDir) throw new Error("base URL, API URL, token, output directory, raw trace path and cached Playwright module are required");
const { chromium } = require(path.join(moduleDir, "playwright"));


function browserArgs() {
  return [
    "--disable-background-networking", "--disable-component-update", "--disable-default-apps",
    "--disable-domain-reliability", "--disable-extensions",
    "--disable-features=OptimizationHints,MediaRouter,ServiceWorker", "--disable-sync",
    "--metrics-recording-only", "--no-first-run", "--no-default-browser-check",
  ];
}


async function waitForShell(page) {
  await page.waitForFunction(() => (
    document.querySelector(".app-shell")?.hidden === false
    && document.body.dataset.pfiReleaseIdentityState === "ready"
  ), null, { timeout: 30_000 });
}


async function waitForReadModelStatusSettlement(page, expected) {
  await page.waitForFunction((settlement) => (
    document.body.dataset.pfiReadModelStatusSettled === "true"
    && document.body.dataset.pfiReadModelStatusSettlement === settlement
  ), expected, { timeout: 30_000 });
}


function watchPage(page, diagnostics) {
  page.on("console", (message) => { if (message.type() === "error") diagnostics.consoleErrors.push(message.text()); });
  page.on("pageerror", (error) => diagnostics.pageErrors.push(String(error?.message || error)));
  page.on("response", (response) => {
    if (response.status() >= 400) diagnostics.httpErrors.push({ status: response.status(), url: response.url() });
  });
}


async function createContext(browser, diagnostics, { sanitizeLineage = false } = {}) {
  const context = await browser.newContext({ locale: "zh-CN", serviceWorkers: "block", viewport: { width: 1440, height: 1100 } });
  const allowedOrigins = new Set([new URL(baseUrl).origin, new URL(apiUrl).origin]);
  await context.route("**/*", async (route) => {
    const requestUrl = route.request().url();
    const parsed = new URL(requestUrl);
    if (sanitizeLineage && parsed.origin === new URL(apiUrl).origin && parsed.pathname === "/api/lineage") {
      diagnostics.requestedOrigins.add(parsed.origin);
      const response = await route.fetch();
      const payload = await response.json();
      for (const metric of payload.metric_drilldown?.metrics || []) metric.value = null;
      payload.contains_private_values = false;
      await route.fulfill({
        status: response.status(),
        contentType: "application/json; charset=utf-8",
        body: JSON.stringify(payload),
      });
      return;
    }
    if (["data:", "blob:", "about:"].includes(parsed.protocol) || allowedOrigins.has(parsed.origin)) {
      if (allowedOrigins.has(parsed.origin)) diagnostics.requestedOrigins.add(parsed.origin);
      await route.continue();
      return;
    }
    diagnostics.blockedExternal.push(requestUrl);
    await route.abort("blockedbyclient");
  });
  return context;
}


async function apiJson(route) {
  const response = await fetch(`${apiUrl}${route}`, {
    headers: { "X-PFI-Runtime-Token": apiToken },
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.message || `${route} failed with ${response.status}`);
  return payload;
}


async function traceValue(page, label) {
  return page.locator(".stage7-metric-trace > div").filter({ has: page.locator("dt", { hasText: label }) }).locator("dd").textContent();
}


const diagnostics = {
  consoleErrors: [], pageErrors: [], httpErrors: [], blockedExternal: [], requestedOrigins: new Set(),
};
const browser = await chromium.launch({ executablePath: chromePath, headless: true, args: browserArgs() });
let result;
try {
  const publicContext = await createContext(browser, diagnostics, { sanitizeLineage: false });
  await publicContext.tracing.start({ screenshots: false, snapshots: false, sources: false });
  const publicPage = await publicContext.newPage();
  watchPage(publicPage, diagnostics);

  await publicPage.goto(`${baseUrl}/settings/parameters`, { waitUntil: "domcontentloaded" });
  await waitForShell(publicPage);
  try {
    await publicPage.waitForFunction(() => (
      document.querySelector('[data-stage7-parameter-center="ready"]')
      || document.querySelector('[data-stage7-lineage-state="error"]')
    ), null, { timeout: 30_000 });
  } catch (_error) {
    // The structured debug below is more actionable than Playwright's timeout.
  }
  if (!await publicPage.locator('[data-stage7-parameter-center="ready"]').count()) {
    const debug = await publicPage.evaluate(() => ({
      route: document.querySelector("#main-workspace")?.dataset.routeAlias || "",
      pageContract: document.querySelector("#main-workspace")?.dataset.stage6PageContract || "",
      bodyState: document.body.dataset.pfiReleaseIdentityState || "",
      lineageText: document.querySelector(".stage7-lineage-surface")?.textContent || "",
      pageKind: document.querySelector("[data-stage7-phase73-page]")?.getAttribute("data-stage7-phase73-page") || "",
    }));
    throw new Error(`parameter center failed: ${JSON.stringify({ debug, diagnostics: { ...diagnostics, requestedOrigins: [...diagnostics.requestedOrigins] } })}`);
  }
  const parameterDomainCount = await publicPage.locator("[data-stage7-parameter-domain]").count();
  const formulaCardCount = await publicPage.locator("[data-stage7-formula-id]").count();
  await publicPage.locator('[data-stage7-parameter-domain="fx"]').click();
  await publicPage.waitForURL(/\/settings\/parameters\?domain=fx$/);
  const parameterRouteUrl = publicPage.url();
  const selectedParameterDomain = await publicPage.locator("[data-stage7-selected-domain]").getAttribute("data-stage7-selected-domain");
  const parameterHashes = await publicPage.locator(".stage7-hash-row dd").allTextContents();
  await publicPage.screenshot({ path: path.join(outputDir, "parameter_center.png"), fullPage: true });

  await publicPage.goto(`${baseUrl}/data/interconnection`, { waitUntil: "domcontentloaded" });
  await waitForShell(publicPage);
  await publicPage.waitForSelector('[data-stage7-interconnection-map="blocked"]', { timeout: 30_000 });
  const mapNodeCount = await publicPage.locator("[data-stage7-interconnection-node]").count();
  const eventTypeRowCount = await publicPage.locator(".stage7-event-types tbody tr").count();
  await publicPage.locator('[data-stage7-interconnection-node="economic_events"]').click();
  await publicPage.waitForURL(/\/data\/interconnection\?node=economic_events$/);
  const selectedMapNode = await publicPage.locator("[data-stage7-selected-node]").getAttribute("data-stage7-selected-node");
  const mapHashes = await publicPage.locator(".stage7-hash-row dd").allTextContents();
  await publicPage.screenshot({ path: path.join(outputDir, "interconnection_map.png"), fullPage: true });

  const metricPage = await publicContext.newPage();
  watchPage(metricPage, diagnostics);
  await metricPage.goto(`${baseUrl}/reports/metric-drilldown?metric=net_worth_cny`, { waitUntil: "domcontentloaded" });
  await waitForShell(metricPage);
  await metricPage.waitForSelector('[data-stage7-metric-drilldown="blocked"]', { timeout: 30_000 });
  const falseZeroCount = await metricPage.locator("[data-stage7-metric-drilldown]").getAttribute("data-stage7-non-ready-false-zero-count");
  const blockedSelected = await metricPage.locator("[data-stage7-selected-metric]").getAttribute("data-stage7-selected-metric");
  const blockedValueText = await metricPage.locator(".stage7-metric-headline > strong").textContent();
  const blockedReasonText = await metricPage.locator(".stage7-metric-headline > p").textContent();
  const blockedFormulaHash = await traceValue(metricPage, "formula hash");
  const blockedParameterHash = await traceValue(metricPage, "parameter hash");
  const blockedDataHash = await traceValue(metricPage, "data hash");
  const blockedReadModelHash = await traceValue(metricPage, "read-model hash");

  await metricPage.locator("[data-stage7-metric-select]").selectOption("living_consumption_cny");
  await metricPage.waitForURL(/metric=living_consumption_cny$/);
  const operationalBlockedSelected = await metricPage.locator("[data-stage7-selected-metric]").getAttribute("data-stage7-selected-metric");
  const operationalBlockedValueText = await metricPage.locator(".stage7-metric-headline > strong").textContent();
  const operationalBlockedReasonText = await metricPage.locator(".stage7-metric-headline > p").textContent();
  const operationalBlockedFormulaHash = await traceValue(metricPage, "formula hash");
  const operationalBlockedParameterHash = await traceValue(metricPage, "parameter hash");
  const operationalBlockedDataHash = await traceValue(metricPage, "data hash");
  const operationalBlockedReadModelHash = await traceValue(metricPage, "read-model hash");
  const operationalBlockedEventHash = await metricPage.locator(".stage7-metric-event-lineage .stage7-hash-row dd").textContent();
  await metricPage.reload({ waitUntil: "domcontentloaded" });
  await waitForShell(metricPage);
  await metricPage.waitForSelector('[data-stage7-selected-metric="living_consumption_cny"]', { timeout: 30_000 });
  const reloadSelected = await metricPage.locator("[data-stage7-metric-select]").inputValue();

  const apiPayload = await apiJson("/api/lineage");
  const runtimeStatusPayload = await apiJson("/api/read-model-status");
  const apiMetrics = apiPayload.metric_drilldown?.metrics || [];
  const apiBlocked = apiMetrics.find((item) => item.metric_id === "net_worth_cny");
  const apiOperationalBlocked = apiMetrics.find((item) => item.metric_id === "living_consumption_cny");
  await publicPage.goto(`${baseUrl}/overview`, { waitUntil: "domcontentloaded" });
  await waitForShell(publicPage);
  await waitForReadModelStatusSettlement(publicPage, "api_canonical");
  const homeStatusSettlement = await publicPage.locator("body").getAttribute("data-pfi-read-model-status-settlement");
  const homeCardTexts = await publicPage.locator("[data-home-card]").allTextContents();
  const homeCardNumericFields = await publicPage.locator("[data-home-card]").evaluateAll((cards) => cards.map((card) => ({
    label: card.querySelector("span")?.textContent || "",
    redacted_value: (card.querySelector("[data-card-value]")?.textContent || "").replace(/[0-9.,-]/g, "#"),
    value: /CNY\s+-?[0-9]/.test(card.querySelector("[data-card-value]")?.textContent || ""),
    detail: /CNY\s+-?[0-9]/.test(card.querySelector("[data-card-detail]")?.textContent || ""),
  })));
  const homeCardText = homeCardTexts.join(" ");
  const fallbackPage = await publicContext.newPage();
  await fallbackPage.route("**/api/read-model-status", (route) => route.abort("failed"));
  await fallbackPage.goto(`${baseUrl}/overview`, { waitUntil: "domcontentloaded" });
  await waitForShell(fallbackPage);
  await waitForReadModelStatusSettlement(fallbackPage, "api_error_fallback");
  const fallbackStatusSettlement = await fallbackPage.locator("body").getAttribute("data-pfi-read-model-status-settlement");
  const fallbackHomeCardTexts = await fallbackPage.locator("[data-home-card]").allTextContents();
  const fallbackHomeCardNumericFields = await fallbackPage.locator("[data-home-card]").evaluateAll((cards) => cards.map((card) => ({
    label: card.querySelector("span")?.textContent || "",
    redacted_value: (card.querySelector("[data-card-value]")?.textContent || "").replace(/[0-9.,-]/g, "#"),
    value: /CNY\s+-?[0-9]/.test(card.querySelector("[data-card-value]")?.textContent || ""),
    detail: /CNY\s+-?[0-9]/.test(card.querySelector("[data-card-detail]")?.textContent || ""),
  })));
  const fallbackHomeCardText = fallbackHomeCardTexts.join(" ");
  await fallbackPage.close();
  const legacyPage = await publicContext.newPage();
  await legacyPage.route("**/api/read-model-status", (route) => route.fulfill({
    status: 200,
    contentType: "application/json; charset=utf-8",
    body: JSON.stringify({
      schema: "PFIV024Stage4ReadModelStatusV1",
      target_version: "v0.2.5",
      stage: "Stage 5",
      contract_version: "PFI-V025-LEGACY-FINANCIAL-PUBLICATION",
      stage7_operational_authority: false,
      legacy_metadatabase_suppressed: false,
      source: { type: "MetaDatabase", status: "ready" },
      core_metric_states: [{
        metric_id: "net_worth_cny", value: 987654.32, currency: "CNY",
        status: "ready", calculation_state: "ready",
      }],
      stage5_financial_model: {
        components: [
          "total_consumption_outflow_cny", "living_consumption_cny",
          "investment_funding_outflow_cny", "investment_allocation_amount_cny",
        ].map((metric_id) => ({ metric_id, status: "ready", value: "987654.32" })),
      },
    }),
  }));
  await legacyPage.goto(`${baseUrl}/overview`, { waitUntil: "domcontentloaded" });
  await waitForShell(legacyPage);
  await waitForReadModelStatusSettlement(legacyPage, "api_rejected_fallback");
  const legacyStatusSettlement = await legacyPage.locator("body").getAttribute("data-pfi-read-model-status-settlement");
  const legacyHomeCardTexts = await legacyPage.locator("[data-home-card]").allTextContents();
  const legacyHomeCardNumericFields = await legacyPage.locator("[data-home-card]").evaluateAll((cards) => cards.map((card) => ({
    label: card.querySelector("span")?.textContent || "",
    redacted_value: (card.querySelector("[data-card-value]")?.textContent || "").replace(/[0-9.,-]/g, "#"),
    value: /CNY\s+-?[0-9]/.test(card.querySelector("[data-card-value]")?.textContent || ""),
    detail: /CNY\s+-?[0-9]/.test(card.querySelector("[data-card-detail]")?.textContent || ""),
  })));
  const legacyHomeCardText = legacyHomeCardTexts.join(" ");
  await legacyPage.close();
  await publicContext.tracing.stop({ path: rawTrace });
  await publicContext.close();

  const hashPattern = /^sha256:[0-9a-f]{64}$/;
  const canonicalRuntimeStatusDiagnostics = {
    api_blocked_value_null: apiBlocked?.value === null,
    api_blocked_reason_present: Boolean(apiBlocked?.blocking_reason_zh),
    runtime_stage7_authority: runtimeStatusPayload?.stage7_operational_authority === true,
    runtime_legacy_suppressed: runtimeStatusPayload?.legacy_metadatabase_suppressed === true,
    runtime_core_metrics_null: (runtimeStatusPayload?.core_metric_states || []).every((item) => item?.value === null),
    home_refresh_settled: homeStatusSettlement === "api_canonical",
    home_has_no_legacy_source: !homeCardText.includes("MetaDatabase"),
    home_has_no_financial_number: !/CNY\s+-?[0-9]/.test(homeCardText),
    fallback_has_no_legacy_source: !fallbackHomeCardText.includes("MetaDatabase"),
    fallback_has_no_financial_number: !/CNY\s+-?[0-9]/.test(fallbackHomeCardText),
    fallback_refresh_settled: fallbackStatusSettlement === "api_error_fallback",
    legacy_200_has_no_legacy_source: !legacyHomeCardText.includes("MetaDatabase"),
    legacy_200_has_no_financial_number: !/CNY\s+-?[0-9]/.test(legacyHomeCardText),
    legacy_200_refresh_settled: legacyStatusSettlement === "api_rejected_fallback",
    home_financial_number_card_indices: homeCardTexts.flatMap((text, index) => /CNY\s+-?[0-9]/.test(text) ? [index] : []),
    fallback_financial_number_card_indices: fallbackHomeCardTexts.flatMap((text, index) => /CNY\s+-?[0-9]/.test(text) ? [index] : []),
    home_financial_number_fields: homeCardNumericFields,
    fallback_financial_number_fields: fallbackHomeCardNumericFields,
    legacy_200_financial_number_card_indices: legacyHomeCardTexts.flatMap((text, index) => /CNY\s+-?[0-9]/.test(text) ? [index] : []),
    legacy_200_financial_number_fields: legacyHomeCardNumericFields,
  };
  const checks = {
    parameter_route_formal: selectedParameterDomain === "fx" && parameterRouteUrl.endsWith("/settings/parameters?domain=fx"),
    parameter_center_chinese_readable: parameterDomainCount >= 15 && formulaCardCount === 20,
    parameter_hashes_visible: parameterHashes.slice(0, 2).every((value) => hashPattern.test(String(value || ""))),
    interconnection_route_formal_and_clickable: selectedMapNode === "economic_events",
    interconnection_nodes_visible: mapNodeCount === 7 && eventTypeRowCount === 0,
    interconnection_hashes_visible: mapHashes.slice(0, 2).every((value) => hashPattern.test(String(value || ""))),
    blocked_metric_selected: blockedSelected === "net_worth_cny",
    blocked_metric_no_false_zero: falseZeroCount === "0" && blockedValueText === "指标阻断，不显示财务零值",
    blocked_reason_visible: Boolean(blockedReasonText?.trim()),
    blocked_hash_contract_visible: [blockedFormulaHash, blockedParameterHash].every((value) => hashPattern.test(String(value || "")))
      && blockedDataHash === "未生成（输入阻断）"
      && blockedReadModelHash === "未生成（输入阻断）",
    operational_metric_selected: operationalBlockedSelected === "living_consumption_cny",
    operational_metric_fail_closed: operationalBlockedValueText === "指标阻断，不显示财务零值"
      && Boolean(operationalBlockedReasonText?.includes("economic_event/interconnection adapter")),
    operational_four_hashes_visible: [operationalBlockedFormulaHash, operationalBlockedParameterHash, operationalBlockedDataHash, operationalBlockedReadModelHash].every((value) => hashPattern.test(String(value || ""))),
    operational_event_lineage_not_fabricated: operationalBlockedEventHash === "未生成（输入阻断）",
    deep_link_reload_restored: reloadSelected === "living_consumption_cny",
    canonical_runtime_status_fail_closed: Object.entries(canonicalRuntimeStatusDiagnostics)
      .filter(([key]) => !key.endsWith("_indices") && !key.endsWith("_fields"))
      .every(([, value]) => value === true),
    api_operational_metric_fail_closed: String(apiOperationalBlocked?.status || "").startsWith("blocked")
      && apiOperationalBlocked?.value === null
      && Boolean(apiOperationalBlocked?.blocking_reason_zh)
      && Object.keys(apiOperationalBlocked?.event_lineage || {}).length === 0,
    no_external_request: diagnostics.blockedExternal.length === 0,
    no_console_error: diagnostics.consoleErrors.length === 0,
    no_page_error: diagnostics.pageErrors.length === 0,
    no_http_error: diagnostics.httpErrors.length === 0,
  };
  result = {
    schema: "PFIV025Stage7Phase73BrowserValidationV1",
    status: Object.values(checks).every(Boolean) ? "pass" : "fail",
    checks,
    parameter_domain_count: parameterDomainCount,
    formula_card_count: formulaCardCount,
    interconnection_node_count: mapNodeCount,
    event_type_row_count: eventTypeRowCount,
    metric_count: Number(apiPayload.metric_drilldown?.metric_count || 0),
    lineage_complete_count: Number(apiPayload.interconnection_map?.lineage_complete_count || 0),
    lineage_missing_count: Number(apiPayload.interconnection_map?.lineage_missing_count || 0),
    requested_origins: [...diagnostics.requestedOrigins].sort(),
    console_errors: diagnostics.consoleErrors,
    page_errors: diagnostics.pageErrors,
    http_errors: diagnostics.httpErrors,
    blocked_external: diagnostics.blockedExternal,
    contains_private_values: false,
    financial_values_persisted: 0,
    finder_used: false,
    canonical_runtime_status_diagnostics: canonicalRuntimeStatusDiagnostics,
  };
  await writeFile(path.join(outputDir, "playwright_result.json"), `${JSON.stringify(result, null, 2)}\n`, "utf8");
} finally {
  await browser.close();
}

if (result?.status !== "pass") throw new Error(JSON.stringify(result, null, 2));
console.log(JSON.stringify({ status: result.status, checks: Object.keys(result.checks).length }));
