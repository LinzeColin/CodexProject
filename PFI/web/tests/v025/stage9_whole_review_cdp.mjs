#!/usr/bin/env node
import { createHash } from "node:crypto";
import { createReadStream } from "node:fs";
import { mkdir, readFile, stat, writeFile } from "node:fs/promises";
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
const decisionData = require(path.join(webRoot, "app/pages/reports/stage9DecisionReviewData.js"));
const analysisData = require(path.join(webRoot, "app/pages/reports/stage9AnalysisData.js"));

const STORAGE_KEY = "pfi-v025-stage9-phase93-human-review";
const FORBIDDEN_MARKERS = ["FORGED_IMMUTABLE_THESIS", "FORGED_EXPORT.html"];
const COMPONENT_LABELS = ["消费总流出", "生活消费", "投资资金流出", "投资域内配置"];
const CONTENT_TYPES = Object.freeze({
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
});

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function sha256(payload) {
  return `sha256:${createHash("sha256").update(payload).digest("hex")}`;
}

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
        response.writeHead(200, {
          "Cache-Control": "no-store",
          "Content-Type": CONTENT_TYPES[extension] || "application/octet-stream",
        });
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

function buildDelta() {
  const contract = decisionData.uiContract;
  return {
    schema: "PFIV025Stage9Phase93ReviewDeltaV1",
    version: "v0.2.5",
    phase_id: "V025-S9-P9.3",
    pack_hash: decisionData.packHash,
    source_analysis_pack_hash: contract.source_analysis_pack_hash,
    export_snapshot_hash: contract.export_snapshot_hash,
    export_manifest_hash: contract.export_manifest_hash,
    review_records: contract.decision_cards.map((decision) => ({
      decision_id: decision.decision_id,
      status: decision.status,
      review_history: clone(decision.review_history),
    })),
  };
}

function diagnosticsRecord() {
  return {
    consoleErrors: [],
    pageErrors: [],
    httpErrors: [],
    blockedExternal: [],
    requestedOrigins: new Set(),
  };
}

function watchPage(page, diagnostics) {
  page.on("console", (message) => { if (message.type() === "error") diagnostics.consoleErrors.push(message.text()); });
  page.on("pageerror", (error) => diagnostics.pageErrors.push(String(error?.message || error)));
  page.on("response", (response) => {
    if (response.status() >= 400) diagnostics.httpErrors.push({ status: response.status(), url: response.url() });
  });
}

async function prepareContext(browser, baseUrl, diagnostics, initialStorage = null) {
  const context = await browser.newContext({
    locale: "zh-CN",
    serviceWorkers: "block",
    viewport: { width: 1440, height: 1200 },
    acceptDownloads: true,
  });
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
  await context.addInitScript(({ key, value, markers }) => {
    try {
      if (value !== null) localStorage.setItem(key, value);
    } catch (_error) { /* actual document origin is required */ }
    window.__pfiForbiddenRendered = false;
    window.addEventListener("DOMContentLoaded", () => {
      const scan = () => {
        const text = document.body?.textContent || "";
        if (markers.some((marker) => text.includes(marker))) window.__pfiForbiddenRendered = true;
      };
      const observer = new MutationObserver(scan);
      if (document.body) observer.observe(document.body, { childList: true, subtree: true, characterData: true });
      scan();
    }, { once: true });
  }, {
    key: STORAGE_KEY,
    value: initialStorage === null ? null : JSON.stringify(initialStorage),
    markers: FORBIDDEN_MARKERS,
  });
  return context;
}

async function waitReady(page) {
  await page.waitForFunction(async () => {
    const analysis = window.PFI_V025_STAGE9_ANALYSIS;
    const decision = window.PFI_V025_STAGE9_DECISION_REVIEW;
    if (
      document.querySelector(".app-shell")?.hidden !== false
      || document.body.dataset.pfiReleaseIdentityState !== "ready"
      || document.body.dataset.v025Stage9Phase92 !== "ready"
      || document.body.dataset.v025Stage9Phase93 !== "ready"
      || document.body.dataset.v025Stage9ComponentCount !== "4"
      || !document.querySelector("[data-stage9-decision-review-panel]")
      || document.body.dataset.v025Stage9ReviewRestore === undefined
    ) return false;
    return analysis?.buildPhase92ViewModel()?.validation?.status === "pass"
      && decision?.buildPhase93ViewModel()?.validation?.status === "pass"
      && (await decision.validateReviewLedger(decision.buildPhase93ViewModel())).status === "pass";
  }, null, { timeout: 30_000 });
  await page.waitForTimeout(150);
}

async function visibleState(page) {
  return page.evaluate((markers) => {
    const api = window.PFI_V025_STAGE9_DECISION_REVIEW;
    const panel = document.querySelector("[data-stage9-decision-review-panel]");
    const bodyText = document.querySelector("#main-workspace")?.textContent || "";
    return {
      routeAlias: document.querySelector("#main-workspace")?.dataset.routeAlias || "",
      restoreState: document.body.dataset.v025Stage9ReviewRestore || "",
      componentCount: Number(document.body.dataset.v025Stage9ComponentCount || 0),
      visibleCardLabels: [...document.querySelectorAll("[data-home-card]")]
        .filter((node) => !node.hidden)
        .map((node) => node.querySelector("span")?.textContent || ""),
      decisionCount: panel?.querySelectorAll("article[data-stage9-decision-id]").length || 0,
      exportButtonCount: panel?.querySelectorAll("button[data-stage9-export-format]").length || 0,
      queueStatus: panel?.querySelector('[data-stage9-decision-id="DEC-PFI-V025-REVIEW-QUEUE"] [data-stage9-decision-status]')
        ?.getAttribute("data-stage9-decision-status") || "",
      canonicalThesis: api.embeddedContract().decision_cards[0].thesis.statement_zh,
      canonicalExportFilename: api.embeddedContract().export_cards[0].filename,
      bodyText,
      forbiddenRendered: Boolean(window.__pfiForbiddenRendered)
        || markers.some((marker) => bodyText.includes(marker)),
      storagePresent: localStorage.getItem(api.storageKey) !== null,
      stage10Started: api.embeddedContract().stage_10_started === true,
      automaticTradingAllowed: api.embeddedContract().automatic_trading_allowed === true,
      tradeExecutionAvailable: api.embeddedContract().trade_execution_available === true,
    };
  }, FORBIDDEN_MARKERS);
}

async function captureDom(page, name, schema) {
  const payload = await page.evaluate((payloadSchema) => {
    const main = document.querySelector("#main-workspace");
    const ids = [...(main?.querySelectorAll("[id]") || [])].map((node) => node.id);
    const outerHTML = main?.outerHTML || "";
    return {
      schema: payloadSchema,
      source: "rendered_main_workspace_outer_html",
      route: main?.dataset.routeAlias || location.pathname,
      title: document.querySelector("#workspace-title")?.textContent || "",
      component_count: Number(document.body.dataset.v025Stage9ComponentCount || 0),
      duplicate_ids: [...new Set(ids.filter((id, index) => ids.indexOf(id) !== index))],
      outer_html: outerHTML,
      contains_financial_amount: /\bCNY\s+-?[0-9]/.test(outerHTML),
      contains_private_path: /\/Users\/|\/private\/var\/folders\//.test(outerHTML),
    };
  }, schema);
  payload.status = payload.outer_html
    && payload.component_count === 4
    && payload.duplicate_ids.length === 0
    && !payload.contains_financial_amount
    && !payload.contains_private_path ? "pass" : "fail";
  await writeFile(path.join(outputDir, name), `${JSON.stringify(payload, null, 2)}\n`, "utf8");
  return payload;
}

async function captureAccessibility(context, page, name, schema) {
  const devtools = await context.newCDPSession(page);
  await devtools.send("Accessibility.enable");
  const tree = await devtools.send("Accessibility.getFullAXTree");
  const interactiveRoles = new Set(["button", "link", "textbox", "combobox", "checkbox", "radio", "menuitem", "option", "switch", "tab"]);
  const nodes = (tree.nodes || [])
    .filter((node) => !node.ignored && String(node.role?.value || ""))
    .map((node) => ({
      role: String(node.role?.value || ""),
      name: String(node.name?.value || ""),
      description: String(node.description?.value || ""),
      backend_dom_node_id: node.backendDOMNodeId || null,
    }));
  const unnamed = nodes.filter((node) => interactiveRoles.has(node.role) && !node.name.trim());
  const names = nodes.map((node) => node.name).filter(Boolean);
  const payload = {
    schema,
    source: "Accessibility.getFullAXTree",
    status: unnamed.length === 0 && COMPONENT_LABELS.every((label) => names.some((name) => name.includes(label))) ? "pass" : "fail",
    node_count: nodes.length,
    unnamed_interactive_node_count: unnamed.length,
    component_labels_present: Object.fromEntries(COMPONENT_LABELS.map((label) => [label, names.some((name) => name.includes(label))])),
    nodes,
  };
  await writeFile(path.join(outputDir, name), `${JSON.stringify(payload, null, 2)}\n`, "utf8");
  return payload;
}

async function runPreloadScenario(browser, baseUrl, diagnostics, payload) {
  const context = await prepareContext(browser, baseUrl, diagnostics, payload);
  const page = await context.newPage();
  watchPage(page, diagnostics);
  try {
    await page.goto(`${baseUrl}/reports?tab=decision-review`, { waitUntil: "domcontentloaded" });
    await waitReady(page);
    return await visibleState(page);
  } finally {
    await context.close();
  }
}

await mkdir(outputDir, { recursive: true });
const diagnostics = diagnosticsRecord();
const { server, baseUrl } = await startServer();
const browser = await chromium.launch({ executablePath: chromePath, headless: true, args: browserArgs() });
let result;
try {
  const legacy = clone(decisionData.uiContract);
  legacy.decision_cards[0].thesis.statement_zh = FORBIDDEN_MARKERS[0];
  legacy.export_cards[0].filename = FORBIDDEN_MARKERS[1];
  const legacyResult = await runPreloadScenario(browser, baseUrl, diagnostics, legacy);

  const brokenLedger = buildDelta();
  brokenLedger.review_records[0].review_history[0].event_hash = `sha256:${"0".repeat(64)}`;
  const brokenLedgerResult = await runPreloadScenario(browser, baseUrl, diagnostics, brokenLedger);

  const context = await prepareContext(browser, baseUrl, diagnostics);
  await context.tracing.start({ screenshots: false, snapshots: false, sources: false });
  const page = await context.newPage();
  watchPage(page, diagnostics);
  try {
    await page.goto(`${baseUrl}/reports`, { waitUntil: "domcontentloaded" });
    await waitReady(page);
    const analysisVisible = await visibleState(page);
    const analysisDom = await captureDom(page, "phase_9_2_dom_snapshot.json", "PFIV025Stage9WholeReviewPhase92DOMSnapshotV1");
    const analysisAx = await captureAccessibility(context, page, "phase_9_2_accessibility_tree.json", "PFIV025Stage9WholeReviewPhase92AccessibilityTreeV1");
    await page.screenshot({ path: path.join(outputDir, "stage9_analysis_components.png"), fullPage: false });
    await page.locator(".workflow-card").filter({ hasText: "现金流窗口敏感性" }).first().screenshot({
      path: path.join(outputDir, "sensitivity_view.png"),
    });

    await page.goto(`${baseUrl}/reports?tab=decision-review`, { waitUntil: "domcontentloaded" });
    await waitReady(page);
    const queueId = "DEC-PFI-V025-REVIEW-QUEUE";
    await page.locator(`[data-stage9-decision-id="${queueId}"] button[data-stage9-review-outcome="accepted"]`).click();
    await page.waitForSelector(`[data-stage9-decision-id="${queueId}"] [data-stage9-decision-status="accepted"]`);
    const persisted = await page.evaluate(async (decisionId) => {
      const api = window.PFI_V025_STAGE9_DECISION_REVIEW;
      const raw = localStorage.getItem(api.storageKey) || "";
      const delta = JSON.parse(raw || "null");
      const validation = delta ? await api.validateReviewDelta(delta) : { status: "fail" };
      return {
        schema: delta?.schema || "",
        topKeys: Object.keys(delta || {}).sort(),
        serialized: raw,
        recordCount: delta?.review_records?.length || 0,
        reviewedStatus: delta?.review_records?.find((row) => row.decision_id === decisionId)?.status || "",
        validationStatus: validation.status,
        persistedFlag: document.body.dataset.v025Stage9ReviewPersisted || "",
      };
    }, queueId);

    await page.reload({ waitUntil: "domcontentloaded" });
    await waitReady(page);
    await page.waitForSelector(`[data-stage9-decision-id="${queueId}"] [data-stage9-decision-status="accepted"]`, { timeout: 30_000 });
    const restored = await visibleState(page);
    const decisionDom = await captureDom(page, "phase_9_3_dom_snapshot.json", "PFIV025Stage9WholeReviewPhase93DOMSnapshotV1");
    const decisionAx = await captureAccessibility(context, page, "phase_9_3_accessibility_tree.json", "PFIV025Stage9WholeReviewPhase93AccessibilityTreeV1");
    await page.locator("[data-stage9-decision-review-panel]").screenshot({
      path: path.join(outputDir, "stage9_decision_review.png"),
    });

    const assetValidation = await page.evaluate(async () => {
      const api = window.PFI_V025_STAGE9_DECISION_REVIEW;
      return Promise.all(["html", "pdf", "csv", "markdown"].map((format) => api.verifyExportAsset(format)));
    });
    const manifestByFormat = Object.fromEntries(decisionData.uiContract.export_cards.map((item) => [item.format, item]));
    const downloads = [];
    for (const format of ["html", "pdf", "csv", "markdown"]) {
      const downloadPromise = page.waitForEvent("download");
      await page.locator(`button[data-stage9-export-format="${format}"]`).click();
      const download = await downloadPromise;
      const downloadPath = await download.path();
      const payload = await readFile(downloadPath);
      downloads.push({
        format,
        filename: download.suggestedFilename(),
        byteSize: payload.byteLength,
        sha256: sha256(payload),
      });
      await page.waitForFunction((expected) => (
        document.querySelector("[data-stage9-decision-review-panel]")?.dataset.lastExportStatus === expected
      ), `pass:${format}`);
    }

    await page.evaluate((key) => {
      const delta = JSON.parse(localStorage.getItem(key) || "null");
      delta.export_manifest_hash = `sha256:${"0".repeat(64)}`;
      delta.forged_immutable_metadata = "FORGED_IMMUTABLE_THESIS";
      localStorage.setItem(key, JSON.stringify(delta));
    }, STORAGE_KEY);
    await page.reload({ waitUntil: "domcontentloaded" });
    await waitReady(page);
    await page.waitForSelector(`[data-stage9-decision-id="${queueId}"] [data-stage9-decision-status="awaiting_human_review"]`, { timeout: 30_000 });
    const tamperedReload = await visibleState(page);

    const requiredText = [
      ...COMPONENT_LABELS,
      "净资产报告", "现金报告", "投资报告", "消费报告", "现金流报告",
      "FORM-PFI-015", "FORM-PFI-020", "模型验证卡", "来源复核",
      "反方证据", "失效条件", "HTML / PDF / CSV / Markdown 同源导出",
    ];
    const missingRequiredText = requiredText.filter((text) => !analysisVisible.bodyText.includes(text));
    const expectedDeltaKeys = [
      "export_manifest_hash", "export_snapshot_hash", "pack_hash", "phase_id", "review_records",
      "schema", "source_analysis_pack_hash", "version",
    ].sort();
    const forbiddenDeltaFields = ["thesis", "source_ids", "model_versions", "export_cards", "report_cards", "financial_value"];
    const checks = {
      legacy_full_view_model_rejected_before_render: legacyResult.restoreState === "canonical"
        && !legacyResult.storagePresent && legacyResult.queueStatus === "awaiting_human_review"
        && !legacyResult.forbiddenRendered,
      broken_event_ledger_rejected_before_render: brokenLedgerResult.restoreState === "canonical"
        && !brokenLedgerResult.storagePresent && brokenLedgerResult.queueStatus === "awaiting_human_review"
        && !brokenLedgerResult.forbiddenRendered,
      four_components_and_reports_visible: analysisVisible.componentCount === 4
        && COMPONENT_LABELS.every((label) => analysisVisible.visibleCardLabels.includes(label))
        && missingRequiredText.length === 0,
      reviewed_analysis_contract_bound: analysisData.packHash === decisionData.uiContract.source_analysis_pack_hash,
      delta_only_persisted: persisted.schema === "PFIV025Stage9Phase93ReviewDeltaV1"
        && JSON.stringify(persisted.topKeys) === JSON.stringify(expectedDeltaKeys)
        && persisted.recordCount === 2 && persisted.reviewedStatus === "accepted"
        && persisted.validationStatus === "pass" && persisted.persistedFlag === "true"
        && forbiddenDeltaFields.every((field) => !persisted.serialized.includes(`\"${field}\"`)),
      valid_delta_restored_after_reload: restored.restoreState === "verified"
        && restored.queueStatus === "accepted" && restored.storagePresent
        && !restored.forbiddenRendered,
      tampered_identity_and_extra_field_fail_closed: tamperedReload.restoreState === "canonical"
        && tamperedReload.queueStatus === "awaiting_human_review"
        && !tamperedReload.storagePresent && !tamperedReload.forbiddenRendered,
      phase92_dom_and_accessibility_pass: analysisDom.status === "pass" && analysisAx.status === "pass",
      phase93_dom_and_accessibility_pass: decisionDom.status === "pass" && decisionAx.status === "pass",
      four_export_assets_verified: assetValidation.length === 4 && assetValidation.every((item) => item.status === "pass"),
      four_downloads_match_manifest: downloads.length === 4 && downloads.every((item) => (
        item.filename === manifestByFormat[item.format].filename
        && item.byteSize === manifestByFormat[item.format].byte_size
        && item.sha256 === manifestByFormat[item.format].sha256
      )),
      same_snapshot_across_formats: new Set(assetValidation.map((item) => item.sourceSnapshotHash)).size === 1,
      no_public_financial_amount_or_private_path: !/\bCNY\s+-?[0-9]/.test(analysisVisible.bodyText)
        && !/\/Users\/|\/private\/var\/folders\//.test(analysisVisible.bodyText),
      no_trade_or_stage10_capability: !analysisVisible.automaticTradingAllowed
        && !analysisVisible.tradeExecutionAvailable && !analysisVisible.stage10Started,
      no_browser_errors: diagnostics.consoleErrors.length === 0
        && diagnostics.pageErrors.length === 0 && diagnostics.httpErrors.length === 0,
      loopback_only: diagnostics.blockedExternal.length === 0
        && diagnostics.requestedOrigins.size === 1
        && diagnostics.requestedOrigins.has(new URL(baseUrl).origin),
    };
    result = {
      schema: "PFIV025Stage9WholeReviewBrowserResultV1",
      status: Object.values(checks).every(Boolean) ? "pass" : "fail",
      acceptance_id: "ACC-PFI-V025-STAGE9-WHOLE-REVIEW",
      checks,
      checkCount: Object.keys(checks).length,
      passedCheckCount: Object.values(checks).filter(Boolean).length,
      visible: {
        componentLabels: analysisVisible.visibleCardLabels,
        componentCount: analysisVisible.componentCount,
        decisionCount: analysisVisible.decisionCount,
        exportButtonCount: analysisVisible.exportButtonCount,
        missingRequiredText,
        restoredQueueStatus: restored.queueStatus,
        tamperedReloadQueueStatus: tamperedReload.queueStatus,
      },
      persistence: { persisted, restored, tamperedReload, legacyResult, brokenLedgerResult },
      exports: { assetValidation, downloads },
      diagnostics: {
        consoleErrors: diagnostics.consoleErrors,
        pageErrors: diagnostics.pageErrors,
        httpErrors: diagnostics.httpErrors,
        blockedExternal: diagnostics.blockedExternal,
        requestedOrigins: [...diagnostics.requestedOrigins],
      },
      domEvidence: {
        phase92: "phase_9_2_dom_snapshot.json",
        phase93: "phase_9_3_dom_snapshot.json",
      },
      accessibilityEvidence: {
        phase92: "phase_9_2_accessibility_tree.json",
        phase93: "phase_9_3_accessibility_tree.json",
      },
      finderUsed: false,
      launchServicesUsed: false,
      externalNetworkUsed: false,
      financialValuesPersisted: 0,
      containsPrivateValues: false,
      automaticTradingAllowed: false,
      tradeExecutionAvailable: false,
      stage10Started: false,
    };
    await writeFile(path.join(outputDir, "playwright_result.json"), `${JSON.stringify(result, null, 2)}\n`, "utf8");
  } finally {
    await context.tracing.stop({ path: rawTrace });
    await context.close();
  }
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
}

if (result?.status !== "pass") {
  throw new Error(`Stage 9 whole-review browser validation failed: ${JSON.stringify(result)}`);
}
console.log(`stage9 whole-review browser: ${result.passedCheckCount}/${result.checkCount} pass`);
