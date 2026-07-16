#!/usr/bin/env node
import { createRequire } from "node:module";
import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";


const require = createRequire(import.meta.url);
const args = Object.fromEntries(process.argv.slice(2).reduce((pairs, value, index, values) => {
  if (value.startsWith("--")) pairs.push([value.slice(2), values[index + 1]]);
  return pairs;
}, []));
const mode = String(args.mode || "exercise");
const baseUrl = String(args["base-url"] || "").replace(/\/$/, "");
const apiUrl = String(args["api-url"] || "").replace(/\/$/, "");
const apiToken = String(args["api-token"] || "");
const outputDir = path.resolve(String(args["output-dir"] || ""));
const rawTrace = path.resolve(String(args["raw-trace"] || ""));
const chromePath = path.resolve(String(args.chrome || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"));
const moduleDir = process.env.PFI_PLAYWRIGHT_MODULE_DIR;
if (!baseUrl || !apiUrl || !apiToken || !outputDir || !rawTrace || !moduleDir || !["exercise", "restart"].includes(mode)) {
  throw new Error("mode, base URL, API URL, output directory, raw trace path and cached Playwright module are required");
}
const { chromium } = require(path.join(moduleDir, "playwright"));


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
    headers: { "Content-Type": "application/json", "X-PFI-Runtime-Token": apiToken, ...(options.headers || {}) },
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.message || `${route} failed with ${response.status}`);
  return payload;
}


async function waitForShell(page) {
  await page.waitForFunction(() => (
    document.querySelector(".app-shell")?.hidden === false
    && document.body.dataset.pfiReleaseIdentityState === "ready"
  ), null, { timeout: 20_000 });
}


async function createContext(browser, diagnostics) {
  const context = await browser.newContext({ locale: "zh-CN", serviceWorkers: "block", viewport: { width: 1440, height: 1050 } });
  const allowedOrigins = new Set([new URL(baseUrl).origin, new URL(apiUrl).origin]);
  await context.route("**/*", async (route) => {
    const requestUrl = route.request().url();
    const parsed = new URL(requestUrl);
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


function watchPage(page, diagnostics) {
  page.on("console", (message) => { if (message.type() === "error") diagnostics.consoleErrors.push(message.text()); });
  page.on("pageerror", (error) => diagnostics.pageErrors.push(String(error?.message || error)));
  page.on("response", (response) => {
    if (response.status() >= 400) diagnostics.httpErrors.push({ status: response.status(), url: response.url() });
  });
}


async function openHoldings(page) {
  await page.goto(`${baseUrl}/investment/holdings`, { waitUntil: "domcontentloaded" });
  await waitForShell(page);
  await page.waitForSelector("[data-holdings-persistence-panel]:not([hidden])");
  await page.waitForFunction(() => !document.querySelector("[data-holdings-persistence-status]")?.textContent.includes("正在读取"));
}


async function fillFirstHolding(page, quantity, note) {
  const row = page.locator("[data-holdings-rows] tr").first();
  await row.locator('[data-holding-field="instrumentId"]').fill("CONTRACT-SENTINEL");
  await row.locator('[data-holding-field="displayName"]').fill("持久化合同哨兵（非财务验收）");
  await row.locator('[data-holding-field="quantity"]').fill(quantity);
  await row.locator('[data-holding-field="averageCost"]').fill("");
  await row.locator('[data-holding-field="marketPrice"]').fill("");
  await row.locator('[data-holding-field="currency"]').fill("CNY");
  await row.locator('[data-holding-field="portfolioId"]').fill("contract-sentinel");
  await row.locator('[data-holding-field="asOf"]').fill("2026-07-15");
  await row.locator('[data-holding-field="note"]').fill(note);
}


async function waitForHoldingCount(expected) {
  const deadline = Date.now() + 20_000;
  while (Date.now() < deadline) {
    const payload = await apiJson("/api/holdings");
    if (Number(payload.summary?.active_count || 0) === expected) return payload;
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error(`holding count did not become ${expected}`);
}


async function surfaceSyncCheck(page, routeAlias, expectedCount) {
  await page.locator(`[data-primary-entry="true"][data-route-alias="${routeAlias}"]`).click();
  await page.waitForFunction((count) => [...document.querySelectorAll("[data-home-card]")].some((card) => (
    card.hidden === false
    && card.querySelector("span")?.textContent === "持仓同步"
    && card.querySelector("[data-card-value]")?.textContent === `${count} 条`
  )), expectedCount, { timeout: 20_000 });
  return page.locator("[data-home-card]:not([hidden])").filter({ hasText: "持仓同步" }).first().locator("[data-card-detail]").textContent();
}


async function redactHoldingDom(page) {
  await page.evaluate(() => {
    document.querySelectorAll("[data-holding-field]").forEach((input) => {
      input.value = input.dataset.holdingField === "quantity" ? "*" : "已脱敏";
    });
    document.body.dataset.stage7EvidenceRedacted = "true";
  });
}


const diagnostics = {
  consoleErrors: [], pageErrors: [], httpErrors: [], blockedExternal: [], requestedOrigins: new Set(),
};
const browser = await chromium.launch({ executablePath: chromePath, headless: true, args: browserArgs() });
let result;
try {
  const context = await createContext(browser, diagnostics);
  await context.tracing.start({ screenshots: false, snapshots: false, sources: false });
  const page = await context.newPage();
  watchPage(page, diagnostics);

  if (mode === "exercise") {
    await openHoldings(page);
    const initial = await apiJson("/api/holdings");
    await page.locator("[data-holdings-add]").click();
    await fillFirstHolding(page, "2.5", "仅验证 CRUD/SQLite/restart；不作为真实持仓或估值证据");
    await page.locator("[data-holdings-save]").click();
    await page.waitForFunction(() => document.querySelector("[data-holdings-persistence-status]")?.textContent.includes("已写入 SQLite"), null, { timeout: 20_000 });
    const created = await waitForHoldingCount(1);
    const createdRow = created.rows[0];

    await page.reload({ waitUntil: "domcontentloaded" });
    await waitForShell(page);
    await page.waitForSelector("[data-holdings-persistence-panel]:not([hidden])");
    await page.waitForFunction(() => document.querySelectorAll("[data-holding-field=quantity]").length === 1);
    const refreshedQuantity = await page.locator('[data-holding-field="quantity"]').inputValue();
    await page.locator('[data-holding-field="quantity"]').fill("3.75");
    await page.locator('[data-holding-field="note"]').fill("已更新；仍是非财务合同哨兵");
    await page.locator("[data-holdings-save]").click();
    await page.waitForFunction(() => document.querySelector("[data-holdings-persistence-status]")?.textContent.includes("已写入 SQLite"), null, { timeout: 20_000 });
    const updated = await waitForHoldingCount(1);
    const updatedRow = updated.rows[0];

    const homeDetail = await surfaceSyncCheck(page, "/overview", 1);
    const investmentDetail = await surfaceSyncCheck(page, "/investment", 1);
    const reportDetail = await surfaceSyncCheck(page, "/reports", 1);
    const trends = await apiJson("/api/trends");

    await page.locator('[data-primary-entry="true"][data-route-alias="/settings"]').click();
    await page.waitForSelector("[data-settings-feedback-console]:not([hidden])");
    await page.waitForFunction(() => !document.querySelector("[data-settings-save-status]")?.textContent.includes("正在读取"));
    await page.locator('[data-settings-preference="default_account"]').selectOption({ label: "投资复盘" });
    await page.locator('[data-settings-preference="theme_language"]').selectOption({ label: "跟随系统" });
    await page.locator('[data-feedback-toggle="haptic"]').uncheck();
    await page.locator('[data-feedback-toggle="sound"]').check();
    await page.locator('[data-feedback-toggle="motion"]').uncheck();
    await page.locator("[data-settings-save]").click();
    await page.waitForFunction(() => document.querySelector("[data-settings-save-status]")?.textContent.includes("SQLite 已保存"), null, { timeout: 20_000 });
    const settings = await apiJson("/api/settings/preferences");

    await page.reload({ waitUntil: "domcontentloaded" });
    await waitForShell(page);
    await page.waitForSelector("[data-settings-feedback-console]:not([hidden])");
    await page.waitForFunction(() => document.querySelector('[data-settings-preference="default_account"]')?.value === "投资复盘");
    const settingsAfterRefresh = await apiJson("/api/settings/preferences");
    await page.evaluate(() => {
      document.querySelector('[data-settings-preference="default_account"]').value = "已脱敏";
      document.querySelector('[data-settings-preference="theme_language"]').value = "已脱敏";
      document.body.dataset.stage7EvidenceRedacted = "true";
    });
    await page.screenshot({ path: path.join(outputDir, "settings_saved_redacted.png"), fullPage: true });

    await openHoldings(page);
    await redactHoldingDom(page);
    await page.screenshot({ path: path.join(outputDir, "holding_saved_redacted.png"), fullPage: true });
    const checks = {
      initial_sqlite_empty: Number(initial.summary?.active_count || 0) === 0,
      create_persisted: Number(created.summary?.active_count || 0) === 1 && Number(createdRow.revision || 0) === 1,
      refresh_persisted: refreshedQuantity === "2.5",
      update_persisted: String(updatedRow.quantity) === "3.75" && Number(updatedRow.revision || 0) === 2,
      financial_values_fail_closed: updated.projection?.financial_values_emitted === 0
        && updated.projection?.financial_acceptance_input === false
        && updated.projection?.investment?.market_value_cny === null,
      surface_hashes_same: new Set([
        updated.projection?.home?.projection_hash,
        updated.projection?.investment?.projection_hash,
        updated.projection?.report?.projection_hash,
      ]).size === 1,
      home_surface_synced: homeDetail?.includes("估值依赖缺失") === true,
      investment_surface_synced: investmentDetail === homeDetail,
      report_surface_synced: reportDetail === homeDetail,
      canonical_trends_use_stage7_projection: trends.readModel?.holding_source_authority === "v025_sqlite_holding_records"
        && trends.readModel?.holding_projection?.projection_hash === updated.projection?.projection_hash
        && trends.readModel?.investment?.market_value_cny === null,
      settings_persisted: settings.persisted === true && Number(settings.revision || 0) === 1,
      settings_refresh_persisted: settingsAfterRefresh.settings_hash === settings.settings_hash,
      settings_feedback_isolated: await page.locator("[data-settings-feedback-console]").isHidden(),
      saved_draft_not_in_local_storage: await page.evaluate(() => localStorage.getItem("pfi-v021-unsubmitted-holdings-draft") === null),
    };
    result = {
      schema: "PFIV025Stage7Phase72BrowserExerciseV1",
      status: Object.values(checks).every(Boolean) ? "pass" : "fail",
      checks,
      active_count_before: Number(initial.summary?.active_count || 0),
      active_count_after_create: Number(created.summary?.active_count || 0),
      created_revision: Number(createdRow.revision || 0),
      updated_revision: Number(updatedRow.revision || 0),
      projection_hash_after_update: updated.projection?.projection_hash,
      financial_values_emitted: Number(updated.projection?.financial_values_emitted || 0),
      settings_revision: Number(settings.revision || 0),
      settings_hash: settings.settings_hash,
      browser_context_closed_after_run: true,
    };
    await writeFile(path.join(outputDir, "playwright_exercise.json"), `${JSON.stringify(result, null, 2)}\n`, "utf8");
  } else {
    const exercise = JSON.parse(await readFile(path.join(outputDir, "playwright_exercise.json"), "utf8"));
    await openHoldings(page);
    const holdings = await apiJson("/api/holdings");
    const quantityAfterRestart = await page.locator('[data-holding-field="quantity"]').inputValue();
    const projectionHash = holdings.projection?.projection_hash;
    const trends = await apiJson("/api/trends");
    await page.locator('[data-primary-entry="true"][data-route-alias="/settings"]').click();
    await page.waitForSelector("[data-settings-feedback-console]:not([hidden])");
    await page.waitForFunction(() => document.querySelector('[data-settings-preference="default_account"]')?.value === "投资复盘");
    const settings = await apiJson("/api/settings/preferences");

    await openHoldings(page);
    await redactHoldingDom(page);
    await page.screenshot({ path: path.join(outputDir, "restart_persistence_redacted.png"), fullPage: true });
    await page.reload({ waitUntil: "domcontentloaded" });
    await waitForShell(page);
    await page.waitForSelector("[data-holdings-persistence-panel]:not([hidden])");
    await page.locator("[data-holdings-soft-delete-row]").click();
    const deleted = await waitForHoldingCount(0);
    await page.locator('[data-primary-entry="true"][data-route-alias="/settings"]').click();
    await page.waitForSelector("[data-settings-feedback-console]:not([hidden])");
    await page.locator("[data-settings-reset]").click();
    await page.waitForFunction(() => document.querySelector('[data-settings-preference="default_account"]')?.value === "主账户", null, { timeout: 20_000 });
    const resetSettings = await apiJson("/api/settings/preferences");

    const checks = {
      exercise_passed_before_restart: exercise.status === "pass",
      service_restart_holding_exists: Number(holdings.summary?.active_count || 0) === 1,
      service_restart_revision_persisted: Number(holdings.rows?.[0]?.revision || 0) === 2,
      service_restart_edit_persisted: quantityAfterRestart === "3.75",
      service_restart_projection_hash_same: projectionHash === exercise.projection_hash_after_update,
      service_restart_canonical_trends_hash_same: trends.readModel?.holding_projection?.projection_hash === projectionHash,
      browser_reopen_settings_persisted: settings.settings_hash === exercise.settings_hash && Number(settings.revision || 0) === 1,
      delete_persisted: Number(deleted.summary?.active_count || 0) === 0 && Number(deleted.summary?.deleted_count || 0) === 1,
      settings_reset_persisted: resetSettings.preferences?.default_account === "主账户"
        && resetSettings.preferences?.feedback_sound === false
        && Number(resetSettings.revision || 0) === 2,
      no_console_errors: diagnostics.consoleErrors.length === 0,
      no_page_errors: diagnostics.pageErrors.length === 0,
      no_http_errors: diagnostics.httpErrors.length === 0,
      no_external_requests: diagnostics.blockedExternal.length === 0,
    };
    result = {
      schema: "PFIV025Stage7Phase72PlaywrightResultV1",
      status: Object.values(checks).every(Boolean) ? "pass" : "fail",
      checks,
      active_count_after_restart: Number(holdings.summary?.active_count || 0),
      revision_after_restart: Number(holdings.rows?.[0]?.revision || 0),
      projection_hash_after_restart: projectionHash,
      settings_revision_after_restart: Number(settings.revision || 0),
      active_count_after_delete: Number(deleted.summary?.active_count || 0),
      deleted_count_after_delete: Number(deleted.summary?.deleted_count || 0),
      settings_revision_after_reset: Number(resetSettings.revision || 0),
      console_errors: diagnostics.consoleErrors,
      page_errors: diagnostics.pageErrors,
      http_errors: diagnostics.httpErrors,
      blocked_external_requests: diagnostics.blockedExternal,
      requested_origins: [...diagnostics.requestedOrigins].sort(),
      financial_sentinel_counts_as_real_acceptance: false,
      private_values_persisted: false,
      screenshots_redacted: true,
      finder_used: false,
    };
    await writeFile(path.join(outputDir, "playwright_result.json"), `${JSON.stringify(result, null, 2)}\n`, "utf8");
  }
  await context.tracing.stop({ path: rawTrace });
  await context.close();
} finally {
  await browser.close();
}
if (result.status !== "pass") process.exitCode = 2;
