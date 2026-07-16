#!/usr/bin/env node
import { createRequire } from "node:module";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";


const require = createRequire(import.meta.url);
const args = Object.fromEntries(process.argv.slice(2).reduce((pairs, value, index, values) => {
  if (value.startsWith("--")) pairs.push([value.slice(2), values[index + 1]]);
  return pairs;
}, []));
const baseUrl = String(args["base-url"] || "").replace(/\/$/, "");
const apiUrl = String(args["api-url"] || "").replace(/\/$/, "");
const apiToken = String(args["api-token"] || "");
const sourcePath = path.resolve(String(args.source || ""));
const invalidSourcePath = path.resolve(String(args["invalid-source"] || ""));
const outputDir = path.resolve(String(args["output-dir"] || ""));
const rawTrace = path.resolve(String(args["raw-trace"] || ""));
const chromePath = path.resolve(String(args.chrome || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"));
const moduleDir = process.env.PFI_PLAYWRIGHT_MODULE_DIR;
if (!baseUrl || !apiUrl || !apiToken || !sourcePath || !invalidSourcePath || !outputDir || !rawTrace || !moduleDir) {
  throw new Error("base URL, API URL, isolated sources, output directory, raw trace path and cached Playwright module are required");
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


async function waitForLedgerCount(expected) {
  const deadline = Date.now() + 20_000;
  while (Date.now() < deadline) {
    const ledger = await apiJson("/api/ledger");
    if (Number(ledger.ledger_count || 0) === expected) return ledger;
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error(`ledger count did not become ${expected}`);
}


async function redactReviewDom(page) {
  await page.evaluate(() => {
    document.querySelectorAll(".stage7-review-item span").forEach((node) => {
      node.textContent = "真实流水详情已脱敏";
    });
    document.querySelectorAll("[data-upload-file-list] strong").forEach((node) => {
      node.textContent = "real_source_snapshot";
    });
    document.body.dataset.stage7EvidenceRedacted = "true";
  });
}


await mkdir(outputDir, { recursive: true });
const browser = await chromium.launch({ executablePath: chromePath, headless: true, args: browserArgs() });
let result;
let tracedContext;
let traceStarted = false;
try {
  const context = await browser.newContext({ locale: "zh-CN", serviceWorkers: "block", viewport: { width: 1440, height: 1050 } });
  tracedContext = context;
  await context.tracing.start({ screenshots: false, snapshots: false, sources: false });
  traceStarted = true;
  const blockedExternal = [];
  const requestedOrigins = new Set();
  const allowedOrigins = new Set([new URL(baseUrl).origin, new URL(apiUrl).origin]);
  await context.route("**/*", async (route) => {
    const requestUrl = route.request().url();
    const parsed = new URL(requestUrl);
    if (["data:", "blob:", "about:"].includes(parsed.protocol) || allowedOrigins.has(parsed.origin)) {
      if (allowedOrigins.has(parsed.origin)) requestedOrigins.add(parsed.origin);
      await route.continue();
      return;
    }
    blockedExternal.push(requestUrl);
    await route.abort("blockedbyclient");
  });
  const page = await context.newPage();
  const consoleErrors = [];
  const pageErrors = [];
  const httpErrors = [];
  page.on("console", (message) => { if (message.type() === "error") consoleErrors.push(message.text()); });
  page.on("pageerror", (error) => pageErrors.push(String(error?.message || error)));
  page.on("response", (response) => { if (response.status() >= 400) httpErrors.push({ status: response.status(), url: response.url() }); });

  await page.goto(`${baseUrl}/data/upload`, { waitUntil: "domcontentloaded" });
  await waitForShell(page);
  await page.waitForSelector("[data-upload-import-panel]:not([hidden])");
  const ledgerInitial = await apiJson("/api/ledger");
  await page.locator("[data-upload-input]").setInputFiles(sourcePath);
  await page.waitForFunction(() => document.querySelector("[data-upload-status]")?.dataset.uploadState === "preview", null, { timeout: 30_000 });
  const batchId = await page.locator("[data-import-batch-id^='import:']").getAttribute("data-import-batch-id");
  if (!batchId) throw new Error("preview batch id is unavailable");
  const preview = await apiJson(`/api/imports/alipay?batch_id=${encodeURIComponent(batchId)}`);
  const ledgerPreview = await apiJson("/api/ledger");
  await redactReviewDom(page);
  await page.screenshot({ path: path.join(outputDir, "upload_preview_redacted.png"), fullPage: true });

  await page.locator("[data-import-confirm]").click();
  await page.waitForFunction(() => document.querySelector("[data-upload-status]")?.dataset.uploadState === "ready", null, { timeout: 30_000 });
  const ledgerConfirmed = await waitForLedgerCount(Number(preview.transaction_count || 0));
  const queueBefore = await apiJson("/api/imports/review-queue?status=pending");

  await page.locator('[data-primary-entry="true"][data-route-alias="/ledger"]').click();
  await page.waitForSelector("[data-ledger-operation-flow]:not([hidden])");
  await page.waitForFunction(() => document.querySelectorAll(".stage7-review-item input[type='radio']").length > 0, null, { timeout: 20_000 });
  await page.locator(".stage7-review-item input[type='radio']").first().check();
  await page.locator("[data-ledger-category-select]").selectOption("餐饮食品");
  await page.locator("[data-ledger-review-save]").click();
  const expectedAfterReview = Number(queueBefore.pending_count || 0) - 1;
  await page.waitForFunction((expected) => document.querySelectorAll(".stage7-review-item input[type='radio']").length === expected, expectedAfterReview, { timeout: 20_000 });
  const queueAfterReview = await apiJson("/api/imports/review-queue?status=pending");
  await redactReviewDom(page);
  await page.screenshot({ path: path.join(outputDir, "review_resolved_redacted.png"), fullPage: true });
  await page.locator("[data-stage7-review-undo]").click();
  await page.waitForFunction((expected) => document.querySelectorAll(".stage7-review-item input[type='radio']").length === expected, Number(queueBefore.pending_count || 0), { timeout: 20_000 });
  const queueAfterUndo = await apiJson("/api/imports/review-queue?status=pending");

  await page.locator('[data-primary-entry="true"][data-route-alias="/data"]').click();
  await page.waitForSelector("[data-upload-import-panel]:not([hidden])");
  await page.locator("[data-upload-input]").setInputFiles([]);
  await page.locator("[data-upload-input]").setInputFiles(sourcePath);
  await page.waitForFunction(() => [...document.querySelectorAll("[data-import-batch-id] dd")].some((node) => node.textContent.includes("幂等复用")), null, { timeout: 30_000 });
  const ledgerDuplicate = await apiJson("/api/ledger");
  await page.locator("[data-stage7-import-rollback]").click();
  const ledgerRolledBack = await waitForLedgerCount(0);
  await page.waitForSelector("[data-stage7-import-retry]");
  await page.locator("[data-stage7-import-retry]").click();
  await page.waitForFunction(() => document.querySelector("[data-upload-status]")?.dataset.uploadState === "preview", null, { timeout: 30_000 });
  const retried = await apiJson(`/api/imports/alipay?batch_id=${encodeURIComponent(batchId)}`);
  await page.locator("[data-import-confirm]").click();
  const ledgerReconfirmed = await waitForLedgerCount(Number(preview.transaction_count || 0));

  await page.locator("[data-upload-input]").setInputFiles(invalidSourcePath);
  await page.waitForFunction(() => document.querySelector("[data-upload-status]")?.dataset.uploadState === "error", null, { timeout: 30_000 });
  const failureBatchId = await page.locator("[data-import-batch-id^='import:']").getAttribute("data-import-batch-id");
  if (!failureBatchId) throw new Error("failed batch id is unavailable");
  const failed = await apiJson(`/api/imports/alipay?batch_id=${encodeURIComponent(failureBatchId)}`);
  const ledgerAfterFailure = await apiJson("/api/ledger");
  await redactReviewDom(page);
  await page.screenshot({ path: path.join(outputDir, "parse_failure_redacted.png"), fullPage: true });

  const fileSummary = Array.isArray(preview.file_summaries) ? preview.file_summaries[0] || {} : {};
  const mappedFields = new Set((preview.field_mapping || []).map((item) => item.canonical_field));
  const transactionCount = Number(preview.transaction_count || 0);
  const reviewCount = Number(preview.review_count || 0);
  const checks = {
    actual_formal_shell_ready: await page.evaluate(() => document.querySelector(".app-shell")?.hidden === false),
    real_source_detected: fileSummary.source_id === "alipay_daily",
    parser_identified: fileSummary.parser_version === "alipay_bill_csv_v1",
    content_hash_present: /^[a-f0-9]{64}$/.test(String(fileSummary.content_sha256 || "")),
    field_mapping_complete: ["occurred_at", "amount", "currency", "account_id", "description"].every((field) => mappedFields.has(field)),
    preview_did_not_post_ledger: Number(ledgerInitial.ledger_count || 0) === 0 && Number(ledgerPreview.ledger_count || 0) === 0,
    confirm_committed_exact_count: Number(ledgerConfirmed.ledger_count || 0) === transactionCount && transactionCount > 0,
    review_queue_created: Number(queueBefore.pending_count || 0) === reviewCount && reviewCount > 0,
    review_persisted: Number(queueAfterReview.pending_count || 0) === expectedAfterReview,
    review_undo_restored: Number(queueAfterUndo.pending_count || 0) === reviewCount,
    duplicate_upload_idempotent: Number(ledgerDuplicate.ledger_count || 0) === transactionCount,
    rollback_compensated: Number(ledgerRolledBack.ledger_count || 0) === 0,
    retry_restored_preview: retried.status === "preview_ready" && Number(retried.transaction_count || 0) === transactionCount,
    reconfirm_committed_exact_count: Number(ledgerReconfirmed.ledger_count || 0) === transactionCount,
    parse_failure_not_fabricated: failed.status === "failed" && Number(failed.transaction_count || 0) === 0 && Number(failed.ledger_count || 0) === 0,
    parse_failure_preserved_existing_ledger: Number(ledgerAfterFailure.ledger_count || 0) === transactionCount,
    no_console_errors: consoleErrors.length === 0,
    no_page_errors: pageErrors.length === 0,
    no_http_errors: httpErrors.length === 0,
    no_external_requests: blockedExternal.length === 0 && [...requestedOrigins].every((origin) => allowedOrigins.has(origin)),
  };
  result = {
    schema: "PFIV025Stage7Phase71PlaywrightResultV1",
    status: Object.values(checks).every(Boolean) ? "pass" : "fail",
    checks,
    source_detected: fileSummary.source_id,
    parser_version: fileSummary.parser_version,
    source_content_sha256: fileSummary.content_sha256,
    transaction_count: transactionCount,
    review_count: reviewCount,
    date_start: preview.date_start,
    date_end: preview.date_end,
    preview_ledger_count: Number(ledgerPreview.ledger_count || 0),
    confirmed_ledger_count: Number(ledgerConfirmed.ledger_count || 0),
    duplicate_ledger_count: Number(ledgerDuplicate.ledger_count || 0),
    rolled_back_ledger_count: Number(ledgerRolledBack.ledger_count || 0),
    reconfirmed_ledger_count: Number(ledgerReconfirmed.ledger_count || 0),
    pending_before_review: Number(queueBefore.pending_count || 0),
    pending_after_review: Number(queueAfterReview.pending_count || 0),
    pending_after_undo: Number(queueAfterUndo.pending_count || 0),
    console_errors: consoleErrors,
    page_errors: pageErrors,
    http_errors: httpErrors,
    blocked_external_requests: blockedExternal,
    requested_origins: [...requestedOrigins].sort(),
    private_values_persisted: false,
    raw_upload_body_persisted: false,
    screenshots_redacted: true,
    finder_used: false,
  };
  await context.tracing.stop({ path: rawTrace });
  traceStarted = false;
  await context.close();
  tracedContext = undefined;
} finally {
  if (traceStarted && tracedContext) {
    await tracedContext.tracing.stop({ path: rawTrace }).catch(() => {});
  }
  if (tracedContext) await tracedContext.close().catch(() => {});
  await browser.close();
}
await writeFile(path.join(outputDir, "playwright_result.json"), `${JSON.stringify(result, null, 2)}\n`, "utf8");
if (result.status !== "pass") process.exitCode = 2;
