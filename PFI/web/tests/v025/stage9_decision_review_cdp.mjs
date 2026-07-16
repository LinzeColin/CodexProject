#!/usr/bin/env node
import { createReadStream } from "node:fs";
import { mkdir, readFile, stat, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import http from "node:http";
import { createRequire } from "node:module";
import path from "node:path";


const require = createRequire(import.meta.url);
const args = Object.fromEntries(process.argv.slice(2).reduce((pairs, value, index, values) => {
  if (value.startsWith("--")) pairs.push([value.slice(2), values[index + 1]]);
  return pairs;
}, []));
const webRoot = path.resolve(String(args["web-root"] || ""));
const outputDir = path.resolve(String(args["output-dir"] || ""));
const rawTrace = path.resolve(String(args["raw-trace"] || path.join(outputDir, "browser_trace_raw.zip")));
const chromePath = path.resolve(String(args.chrome || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"));
const moduleDir = process.env.PFI_PLAYWRIGHT_MODULE_DIR;
if (!args["web-root"] || !args["output-dir"] || !moduleDir) {
  throw new Error("--web-root, --output-dir and cached PFI_PLAYWRIGHT_MODULE_DIR are required");
}
const { chromium } = require(path.join(moduleDir, "playwright"));

const CONTENT_TYPES = Object.freeze({
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
});

function runtimeConfig(baseUrl) {
  return JSON.stringify({
    apiBaseUrl: baseUrl,
    readModelStatusApi: false,
    runtimeApiEnabled: false,
    releaseManifestApi: false,
    releaseCachePolicyApi: false,
    stage1OfficialCandidate: false,
    candidateDataMode: "canonical",
  });
}

async function transformedIndex(baseUrl) {
  const source = await readFile(path.join(webRoot, "index.html"), "utf8");
  const updated = source.replace(
    /<script type="application\/json" id="pfi-runtime-config">.*?<\/script>/s,
    `<script type="application/json" id="pfi-runtime-config">${runtimeConfig(baseUrl)}</script>`,
  );
  if (updated === source) throw new Error("runtime config seam is unavailable");
  return updated;
}

function staticPath(pathname) {
  const clean = pathname.replace(/^\/+/, "");
  const nestedAsset = clean.match(/(?:^|\/)(app\/.*|styles\/.*|styles\.css)$/)?.[1];
  const candidate = path.resolve(webRoot, nestedAsset || clean);
  return candidate === webRoot || candidate.startsWith(`${webRoot}${path.sep}`) ? candidate : null;
}

async function startServer() {
  let baseUrl = "";
  const server = http.createServer(async (request, response) => {
    try {
      const requestUrl = new URL(request.url || "/", baseUrl || "http://127.0.0.1");
      const candidate = staticPath(decodeURIComponent(requestUrl.pathname));
      let candidateStat = null;
      try { candidateStat = candidate ? await stat(candidate) : null; } catch (_error) { candidateStat = null; }
      const extension = candidateStat?.isFile() ? path.extname(candidate).toLowerCase() : "";
      if (candidateStat?.isFile() && extension !== ".html") {
        response.writeHead(200, { "Cache-Control": "no-store", "Content-Type": CONTENT_TYPES[extension] || "application/octet-stream" });
        createReadStream(candidate).pipe(response);
        return;
      }
      const markup = await transformedIndex(baseUrl);
      response.writeHead(200, {
        "Cache-Control": "no-store",
        "Content-Type": "text/html; charset=utf-8",
        "Content-Length": Buffer.byteLength(markup),
      });
      response.end(markup);
    } catch (error) {
      const body = JSON.stringify({ error: String(error?.message || error) });
      response.writeHead(500, { "Content-Type": "application/json; charset=utf-8" });
      response.end(body);
    }
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const address = server.address();
  if (!address || typeof address === "string") throw new Error("loopback address unavailable");
  baseUrl = `http://127.0.0.1:${address.port}`;
  return { server, baseUrl };
}

function browserArgs() {
  return [
    "--disable-background-networking",
    "--disable-component-update",
    "--disable-default-apps",
    "--disable-domain-reliability",
    "--disable-extensions",
    "--disable-features=OptimizationHints,MediaRouter,ServiceWorker",
    "--disable-sync",
    "--metrics-recording-only",
    "--no-first-run",
    "--no-default-browser-check",
  ];
}

function sha256(payload) {
  return `sha256:${createHash("sha256").update(payload).digest("hex")}`;
}

await mkdir(outputDir, { recursive: true });
const diagnostics = { consoleErrors: [], pageErrors: [], httpErrors: [], blockedExternal: [], requestedOrigins: new Set() };
const { server, baseUrl } = await startServer();
const browser = await chromium.launch({ executablePath: chromePath, headless: true, args: browserArgs() });
let result;
try {
  const context = await browser.newContext({ locale: "zh-CN", serviceWorkers: "block", viewport: { width: 1440, height: 1200 }, acceptDownloads: true });
  const allowedOrigin = new URL(baseUrl).origin;
  await context.route("**/*", async (route) => {
    const requestUrl = route.request().url();
    const parsed = new URL(requestUrl);
    if (["data:", "blob:", "about:"].includes(parsed.protocol) || parsed.origin === allowedOrigin) {
      if (parsed.origin === allowedOrigin) diagnostics.requestedOrigins.add(parsed.origin);
      await route.continue();
      return;
    }
    diagnostics.blockedExternal.push(requestUrl);
    await route.abort("blockedbyclient");
  });
  await context.tracing.start({ screenshots: false, snapshots: false, sources: false });
  const page = await context.newPage();
  page.on("console", (message) => { if (message.type() === "error") diagnostics.consoleErrors.push(message.text()); });
  page.on("pageerror", (error) => diagnostics.pageErrors.push(String(error?.message || error)));
  page.on("response", (response) => { if (response.status() >= 400) diagnostics.httpErrors.push({ status: response.status(), url: response.url() }); });
  await page.goto(`${baseUrl}/reports?tab=decision-review`, { waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => (
    document.querySelector(".app-shell")?.hidden === false
    && document.body.dataset.pfiReleaseIdentityState === "ready"
    && document.body.dataset.v025Stage9Phase92 === "ready"
    && document.body.dataset.v025Stage9Phase93 === "ready"
    && document.querySelector("[data-stage9-decision-review-panel]")
    && window.PFI_V025_STAGE9_DECISION_REVIEW?.buildPhase93ViewModel()?.validation?.status === "pass"
  ), null, { timeout: 30_000 });
  await page.waitForTimeout(200);

  const before = await page.evaluate(async () => {
    const api = window.PFI_V025_STAGE9_DECISION_REVIEW;
    const panel = document.querySelector("[data-stage9-decision-review-panel]");
    const bodyText = document.querySelector("#main-workspace")?.textContent || "";
    return {
      phase92: document.body.dataset.v025Stage9Phase92 || "",
      phase93: document.body.dataset.v025Stage9Phase93 || "",
      routeAlias: document.querySelector("#main-workspace")?.dataset.routeAlias || "",
      decisionCount: panel?.querySelectorAll("article[data-stage9-decision-id]").length || 0,
      outcomeButtonCount: panel?.querySelectorAll("button[data-stage9-review-outcome]").length || 0,
      exportButtonCount: panel?.querySelectorAll("button[data-stage9-export-format]").length || 0,
      workflowCardCount: document.querySelectorAll("[data-workflow-cards] .workflow-card").length,
      bodyText,
      viewValidation: api.validatePhase93ViewModel(api.buildPhase93ViewModel()),
      ledgerValidation: await api.validateReviewLedger(api.buildPhase93ViewModel()),
    };
  });

  const queueId = "DEC-PFI-V025-REVIEW-QUEUE";
  await page.locator(`[data-stage9-decision-id="${queueId}"] button[data-stage9-review-outcome="accepted"]`).click();
  await page.waitForSelector(`[data-stage9-decision-id="${queueId}"] [data-stage9-decision-status="accepted"]`);
  const afterReview = await page.evaluate(async (decisionId) => {
    const api = window.PFI_V025_STAGE9_DECISION_REVIEW;
    const persisted = JSON.parse(localStorage.getItem(api.storageKey) || "null");
    const decision = persisted?.decision_cards?.find((item) => item.decision_id === decisionId);
    return {
      status: decision?.status || "",
      historyCount: decision?.review_history?.length || 0,
      persistedFlag: document.body.dataset.v025Stage9ReviewPersisted || "",
      tradeExecutionAvailable: decision?.trade_execution_available,
      automaticTradingAllowed: decision?.automatic_trading_allowed,
      ledgerValidation: persisted ? await api.validateReviewLedger(persisted) : { status: "fail" },
    };
  }, queueId);

  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForSelector(`[data-stage9-decision-id="${queueId}"] [data-stage9-decision-status="accepted"]`, { timeout: 30_000 });
  const afterReload = await page.evaluate((decisionId) => {
    const card = document.querySelector(`[data-stage9-decision-id="${decisionId}"]`);
    return {
      status: card?.querySelector("[data-stage9-decision-status]")?.getAttribute("data-stage9-decision-status") || "",
      availableOutcomes: [...(card?.querySelectorAll("button[data-stage9-review-outcome]") || [])].map((button) => button.dataset.stage9ReviewOutcome),
      bodyText: document.querySelector("#main-workspace")?.textContent || "",
    };
  }, queueId);

  const assetValidation = await page.evaluate(async () => {
    const api = window.PFI_V025_STAGE9_DECISION_REVIEW;
    return Promise.all(["html", "pdf", "csv", "markdown"].map((format) => api.verifyExportAsset(format)));
  });
  const downloads = [];
  for (const format of ["html", "pdf", "csv", "markdown"]) {
    const downloadPromise = page.waitForEvent("download");
    await page.locator(`button[data-stage9-export-format="${format}"]`).click();
    const download = await downloadPromise;
    const downloadPath = await download.path();
    const payload = await readFile(downloadPath);
    downloads.push({ format, filename: download.suggestedFilename(), byteSize: payload.byteLength, sha256: sha256(payload) });
    await page.waitForFunction((expected) => document.querySelector("[data-stage9-decision-review-panel]")?.dataset.lastExportStatus === expected, `pass:${format}`);
  }

  const panel = page.locator("[data-stage9-decision-review-panel]");
  await panel.scrollIntoViewIfNeeded();
  await page.waitForTimeout(100);
  await page.screenshot({ path: path.join(outputDir, "decision_review_view.png"), fullPage: true });
  await context.tracing.stop({ path: rawTrace });

  const manifestByFormat = Object.fromEntries(await page.evaluate(() => (
    window.PFI_V025_STAGE9_DECISION_REVIEW.embeddedContract().export_cards.map((item) => [item.format, item])
  )));
  const requiredText = ["人工复核", "反方证据", "失效条件", "接受只记录人工复核结果，不触发交易", "HTML / PDF / CSV / Markdown 同源导出", "Stage 9 整阶段审查"];
  const missingRequiredText = requiredText.filter((text) => !before.bodyText.includes(text));
  const checks = {
    phase_contract_ready: before.phase92 === "ready" && before.phase93 === "ready" && before.viewValidation.status === "pass" && before.ledgerValidation.status === "pass",
    reports_route_mounted: before.routeAlias.startsWith("/reports"),
    two_review_decisions_visible: before.decisionCount === 2,
    all_human_outcomes_available: before.outcomeButtonCount === 8,
    counter_evidence_and_invalidation_visible: missingRequiredText.length === 0,
    phase92_report_workflow_preserved: before.workflowCardCount === 29 && afterReload.bodyText.includes("3 blocked / 2 partial"),
    accepted_review_is_audited: afterReview.status === "accepted" && afterReview.historyCount === 2 && afterReview.ledgerValidation.status === "pass",
    accepted_review_has_no_execution: afterReview.tradeExecutionAvailable === false && afterReview.automaticTradingAllowed === false,
    review_persists_after_reload: afterReview.persistedFlag === "true" && afterReload.status === "accepted" && JSON.stringify(afterReload.availableOutcomes) === JSON.stringify(["invalidated"]),
    four_export_assets_verified: before.exportButtonCount === 4 && assetValidation.length === 4 && assetValidation.every((item) => item.status === "pass"),
    four_downloads_match_manifest: downloads.length === 4 && downloads.every((item) => item.filename === manifestByFormat[item.format].filename && item.byteSize === manifestByFormat[item.format].byte_size && item.sha256 === manifestByFormat[item.format].sha256),
    same_snapshot_across_formats: new Set(assetValidation.map((item) => item.sourceSnapshotHash)).size === 1,
    no_financial_amount_visible: !/\bCNY\s+-?[0-9]/.test(afterReload.bodyText),
    no_trade_or_whole_stage_claim: !/自动交易已启用|直接下单|整阶段审查已通过/.test(afterReload.bodyText) && afterReload.bodyText.includes("尚未开始"),
    no_browser_errors: diagnostics.consoleErrors.length === 0 && diagnostics.pageErrors.length === 0 && diagnostics.httpErrors.length === 0,
    loopback_only: diagnostics.blockedExternal.length === 0 && diagnostics.requestedOrigins.size === 1 && diagnostics.requestedOrigins.has(allowedOrigin),
  };
  result = {
    schema: "PFIV025Stage9Phase93BrowserResultV1",
    status: Object.values(checks).every(Boolean) ? "pass" : "fail",
    checks,
    checkCount: Object.keys(checks).length,
    passedCheckCount: Object.values(checks).filter(Boolean).length,
    visible: {
      phase92: before.phase92,
      phase93: before.phase93,
      routeAlias: before.routeAlias,
      decisionCount: before.decisionCount,
      outcomeButtonCount: before.outcomeButtonCount,
      exportButtonCount: before.exportButtonCount,
      workflowCardCount: before.workflowCardCount,
      missingRequiredText,
      acceptedStatus: afterReload.status,
      acceptedAvailableOutcomes: afterReload.availableOutcomes,
    },
    downloads,
    diagnostics: {
      consoleErrors: diagnostics.consoleErrors,
      pageErrors: diagnostics.pageErrors,
      httpErrors: diagnostics.httpErrors,
      blockedExternal: diagnostics.blockedExternal,
      requestedOriginCount: diagnostics.requestedOrigins.size,
    },
    finderUsed: false,
    launchServicesUsed: false,
    externalNetworkUsed: false,
    financialValuesPersisted: 0,
    containsPrivateValues: false,
    automaticTradingAllowed: false,
    tradeExecutionAvailable: false,
  };
  await writeFile(path.join(outputDir, "playwright_result.json"), `${JSON.stringify(result, null, 2)}\n`, "utf8");
  await context.close();
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
}
if (result?.status !== "pass") {
  throw new Error(`Stage 9 Phase 9.3 browser validation failed: ${JSON.stringify(result)}`);
}
console.log(`stage9 phase 9.3 browser: ${result.passedCheckCount}/${result.checkCount} pass`);
