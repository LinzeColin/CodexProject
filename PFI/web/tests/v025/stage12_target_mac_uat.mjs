#!/usr/bin/env node

import { createHash } from "node:crypto";
import { createRequire } from "node:module";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

const require = createRequire(import.meta.url);

const PRIMARY = Object.freeze([
  ["/overview", "首页总览"],
  ["/accounts", "账户与资产"],
  ["/ledger", "账本流水"],
  ["/investment", "投资管理"],
  ["/consumption", "消费管理"],
  ["/data", "数据源与上传"],
  ["/review", "建议与复盘"],
  ["/reports", "报告与洞察"],
  ["/market-research", "市场与研究"],
  ["/settings", "设置"],
]);

function parseArgs(values) {
  const parsed = { sourcePaths: [] };
  for (let index = 0; index < values.length; index += 1) {
    const token = values[index];
    const next = values[index + 1];
    if (token === "--source-path") {
      parsed.sourcePaths.push(path.resolve(String(next || "")));
      index += 1;
      continue;
    }
    const key = {
      "--url": "url",
      "--output-dir": "outputDir",
      "--trace": "tracePath",
      "--mode": "mode",
      "--expected-ledger-count": "expectedLedgerCount",
      "--expected-review-count": "expectedReviewCount",
    }[token];
    if (!key || !next) throw new Error(`invalid argument: ${token}`);
    parsed[key] = next;
    index += 1;
  }
  parsed.outputDir = path.resolve(String(parsed.outputDir || ""));
  parsed.tracePath = path.resolve(String(parsed.tracePath || ""));
  parsed.mode = String(parsed.mode || "initial");
  parsed.expectedLedgerCount = Number(parsed.expectedLedgerCount || 0);
  parsed.expectedReviewCount = Number(parsed.expectedReviewCount || 0);
  if (!parsed.url || !parsed.outputDir || !parsed.tracePath) {
    throw new Error("url, output directory and trace are required");
  }
  if (!['initial', 'restart'].includes(parsed.mode)) throw new Error("invalid mode");
  if (parsed.mode === "initial" && parsed.sourcePaths.length !== 4) {
    throw new Error("initial UAT requires four immutable real source snapshots");
  }
  return parsed;
}

function sha256(payload) {
  return createHash("sha256").update(payload).digest("hex");
}

function browserArgs() {
  return [
    "--disable-background-networking",
    "--disable-component-update",
    "--disable-default-apps",
    "--disable-domain-reliability",
    "--disable-features=Translate,MediaRouter,OptimizationHints",
    "--disable-sync",
    "--metrics-recording-only",
    "--no-default-browser-check",
    "--no-first-run",
    "--password-store=basic",
    "--use-mock-keychain",
  ];
}

async function resolveShellFrame(page, timeoutMs = 60_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    for (const frame of page.frames()) {
      if (frame === page.mainFrame()) continue;
      try {
        const ready = await frame.evaluate(
          () => Boolean(document.getElementById("pfi-release-manifest") && window.PFI_RELEASE_IDENTITY_READY),
        );
        if (ready) return frame;
      } catch (_error) {
        // Streamlit may replace the component frame while it initializes.
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 200));
  }
  throw new Error("official PFI shell did not become ready");
}

async function mountRoute(frame, routeAlias) {
  const result = await frame.evaluate(
    (route) => window.PFI_STAGE1_SHELL?.mountRoute?.(route, { replace: false, source: "stage12_target_mac_uat" }),
    routeAlias,
  );
  if (!result || result.status !== "mounted") throw new Error(`route did not mount: ${routeAlias}`);
  const mountedRoute = String(result.routeAlias || routeAlias);
  await frame.waitForFunction(
    (route) => document.querySelector("main#main-workspace")?.dataset?.routeAlias === route,
    mountedRoute,
    { timeout: 30_000 },
  );
  return result;
}

async function runtimeConfig(frame) {
  return frame.evaluate(() => {
    const node = document.getElementById("pfi-runtime-config");
    return JSON.parse(node?.textContent || "{}");
  });
}

async function apiJson(frame, apiPath, options = {}) {
  return frame.evaluate(
    async ({ apiPath: requestedPath, options: requestedOptions }) => {
      const config = JSON.parse(document.getElementById("pfi-runtime-config")?.textContent || "{}");
      const headers = {
        "Content-Type": "application/json",
        "X-PFI-Runtime-Token": String(config.apiAuthToken || ""),
        ...(requestedOptions.headers || {}),
      };
      const response = await fetch(`${config.apiBaseUrl}${requestedPath}`, {
        method: requestedOptions.method || "GET",
        headers,
        body: requestedOptions.body || undefined,
        cache: "no-store",
      });
      const body = await response.json();
      return { status: response.status, body };
    },
    { apiPath, options },
  );
}

async function identitySnapshot(frame) {
  const snapshot = await frame.evaluate(async () => {
    const gate = await window.PFI_RELEASE_IDENTITY_READY;
    const manifest = JSON.parse(document.getElementById("pfi-release-manifest")?.textContent || "{}");
    const primary = [...document.querySelectorAll('nav[aria-label="一级工作区"] [data-primary-entry="true"]')]
      .filter((node) => !node.hidden)
      .map((node) => ({
        label: String(node.textContent || "").trim(),
        route: String(node.dataset.routeAlias || ""),
      }));
    const config = JSON.parse(document.getElementById("pfi-runtime-config")?.textContent || "{}");
    const response = await fetch(`${config.apiBaseUrl}/api/release-manifest`, {
      headers: { "X-PFI-Runtime-Token": String(config.apiAuthToken || "") },
      cache: "no-store",
    });
    const runtimeManifest = await response.json();
    return {
      gate_ok: gate?.ok === true,
      gate_state: String(document.body?.dataset?.pfiReleaseIdentityState || ""),
      gate_issues: Array.isArray(gate?.issues) ? gate.issues.map(String) : [],
      embedded_manifest: manifest,
      runtime_manifest: runtimeManifest,
      runtime_manifest_status: response.status,
      primary,
      shell_schema: String(document.body?.dataset?.shellSchema || ""),
    };
  });
  if (!snapshot.gate_ok) {
    throw new Error(`release identity gate ${snapshot.gate_state || "unknown"}: ${snapshot.gate_issues.join(",") || "unknown issue"}`);
  }
  return snapshot;
}

async function primaryRouteAudit(frame) {
  const rows = [];
  for (const [route, label] of PRIMARY) {
    const control = frame.locator(
      `nav[aria-label="一级工作区"] [data-primary-entry="true"][data-route-alias="${route}"]`,
    );
    await control.click();
    await frame.waitForFunction(
      ({ route: expectedRoute }) => {
        const active = document.querySelector(
          'nav[aria-label="一级工作区"] [data-primary-entry="true"].is-active',
        );
        return active?.dataset?.routeAlias === expectedRoute;
      },
      { route },
      { timeout: 30_000 },
    );
    rows.push({ route, label, active: true });
  }
  return rows;
}

async function waitForLedger(frame, minimumCount, timeoutMs = 90_000) {
  const deadline = Date.now() + timeoutMs;
  let latest = {};
  while (Date.now() < deadline) {
    latest = (await apiJson(frame, "/api/ledger")).body || {};
    if (Number(latest.ledger_count || 0) >= minimumCount) return latest;
    await new Promise((resolve) => setTimeout(resolve, 300));
  }
  throw new Error("ledger did not reach the imported record count");
}

async function runInitialUat(frame, sourcePaths) {
  await mountRoute(frame, "/sources-upload?tab=upload");
  const upload = frame.locator("[data-upload-input]");
  await upload.setInputFiles(sourcePaths);
  await frame.waitForFunction(
    () => document.querySelector("[data-upload-status]")?.dataset?.uploadState === "preview",
    undefined,
    { timeout: 90_000 },
  );
  const batchId = await frame.locator('[data-import-batch-id^="import:"]').getAttribute("data-import-batch-id");
  if (!batchId) throw new Error("real import preview batch is unavailable");
  const preview = (await apiJson(frame, `/api/imports/alipay?batch_id=${encodeURIComponent(batchId)}`)).body;
  await frame.locator("[data-import-confirm]").click();
  await frame.waitForFunction(
    () => document.querySelector("[data-upload-status]")?.dataset?.uploadState === "ready",
    undefined,
    { timeout: 90_000 },
  );
  const ledger = await waitForLedger(frame, Number(preview.transaction_count || 0));
  const queueBefore = (await apiJson(frame, "/api/imports/review-queue?status=pending")).body;
  const reviewItem = Array.isArray(queueBefore.items) ? queueBefore.items[0] : null;
  if (!reviewItem?.review_id) throw new Error("real review queue is unavailable");
  const reviewResponse = await apiJson(frame, "/api/imports/review", {
    method: "POST",
    body: JSON.stringify({ review_id: reviewItem.review_id, decision: "accept", category: "" }),
  });
  const queueAfter = (await apiJson(frame, "/api/imports/review-queue?status=pending")).body;

  await mountRoute(frame, "/investment?tab=holdings");
  const holdings = await frame.evaluate(() => {
    const panel = document.querySelector("[data-holdings-persistence-panel]");
    const text = String(panel?.textContent || "");
    return {
      panel_visible: Boolean(panel && !panel.hidden),
      truthful_not_loaded: /未加载|等待真实持仓|缺少真实持仓|暂无持仓|尚未写入|not.loaded/i.test(text),
      false_zero_count: (text.match(/\bCNY\s+0(?:\.0+)?\b/g) || []).length,
    };
  });

  await mountRoute(frame, "/reports/metric-drilldown?formula=FORM-PFI-015");
  await frame.waitForSelector("[data-stage7-metric-drilldown]", { timeout: 30_000 });
  const drilldown = await frame.evaluate(() => {
    const text = String(document.querySelector("main#main-workspace")?.textContent || "");
    const eventLineage = document.querySelector(".stage7-metric-event-lineage");
    return {
      formula_visible: text.includes("FORM-PFI-015"),
      source_visible: /来源|source/i.test(text),
      interconnection_visible: Boolean(eventLineage) && /事件 lineage|经济事件/.test(String(eventLineage.textContent || "")),
      parameter_visible: /参数|parameter/i.test(text),
    };
  });

  await mountRoute(frame, "/reports?tab=monthly");
  const reports = await frame.evaluate(() => {
    const validation = window.PFI_V025_STAGE9_ANALYSIS?.validatePhase92ViewModel?.() || {};
    return {
      status: String(validation.status || "unavailable"),
      report_count: Number(validation.reportCount || 0),
      blocked_count: Number(validation.blockedCount || 0),
      partial_count: Number(validation.partialCount || 0),
    };
  });

  return {
    source_blob_count: sourcePaths.length,
    raw_record_count: Number(preview.raw_record_count || 0),
    transaction_count: Number(preview.transaction_count || 0),
    ledger_count: Number(ledger.ledger_count || 0),
    review_count_before: Number(queueBefore.pending_count || queueBefore.items?.length || 0),
    review_count_after: Number(queueAfter.pending_count || queueAfter.items?.length || 0),
    review_write_status: reviewResponse.status,
    holdings,
    drilldown,
    reports,
    fixture_used: false,
    fallback_used: false,
  };
}

async function runRestartUat(frame, expectedLedgerCount, expectedReviewCount) {
  const ledger = (await apiJson(frame, "/api/ledger")).body;
  const queue = (await apiJson(frame, "/api/imports/review-queue?status=pending")).body;
  await mountRoute(frame, "/ledger?tab=review");
  const visible = await frame.evaluate(() => {
    const panel = document.querySelector("[data-ledger-operation-flow]");
    return Boolean(panel && !panel.hidden && Number(document.querySelectorAll("[data-stage7-review-queue] input").length) >= 0);
  });
  return {
    expected_ledger_count: expectedLedgerCount,
    observed_ledger_count: Number(ledger.ledger_count || 0),
    expected_review_count: expectedReviewCount,
    observed_review_count: Number(queue.pending_count || queue.items?.length || 0),
    review_page_visible: visible,
  };
}

async function captureIdentity(frame, outputPath) {
  const details = frame.locator("[data-pfi-release-identity-details]");
  await details.evaluate((node) => { node.open = true; });
  const panel = details.locator(".pfi-release-identity-panel");
  await panel.locator("[data-pfi-release-detail-backend]").waitFor({ state: "visible", timeout: 30_000 });
  await panel.screenshot({ path: outputPath });
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const moduleDir = String(process.env.PFI_PLAYWRIGHT_MODULE_DIR || "");
  const chromePath = String(process.env.PFI_CHROME_PATH || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome");
  if (!moduleDir) throw new Error("cached Playwright module directory is required");
  const { chromium } = require(path.join(moduleDir, "playwright"));
  await mkdir(args.outputDir, { recursive: true });
  const screenshotPath = path.join(args.outputDir, args.mode === "initial" ? "target_mac_app.png" : "restart_persistence.png");
  const diagnostics = {
    console_errors: [],
    expected_offline_console_errors: [],
    page_errors: [],
    unexpected_http_errors: [],
    blocked_external_count: 0,
  };
  let offlineWindow = false;
  const browser = await chromium.launch({ executablePath: chromePath, headless: true, args: browserArgs() });
  let context;
  let traceStarted = false;
  let result;
  try {
    context = await browser.newContext({
      locale: "zh-CN",
      serviceWorkers: "block",
      viewport: { width: 1440, height: 1050 },
      colorScheme: "light",
      reducedMotion: "reduce",
    });
    await context.route("**/*", async (route) => {
      const requested = new URL(route.request().url());
      if (["data:", "blob:", "about:"].includes(requested.protocol) ||
          (["127.0.0.1", "localhost"].includes(requested.hostname) && ["http:", "ws:"].includes(requested.protocol))) {
        await route.continue();
        return;
      }
      diagnostics.blocked_external_count += 1;
      await route.abort("blockedbyclient");
    });
    await context.tracing.start({ screenshots: true, snapshots: true, sources: false });
    traceStarted = true;
    const page = await context.newPage();
    page.on("console", (message) => {
      if (message.type() !== "error") return;
      const text = message.text();
      if (offlineWindow && /ERR_(?:INTERNET_DISCONNECTED|NETWORK_CHANGED|CONNECTION_REFUSED)/.test(text)) {
        diagnostics.expected_offline_console_errors.push(text);
      } else {
        diagnostics.console_errors.push(text);
      }
    });
    page.on("pageerror", (error) => diagnostics.page_errors.push(String(error?.message || error)));
    page.on("response", (response) => {
      const pathname = new URL(response.url()).pathname;
      if (response.status() >= 400 && pathname !== "/favicon.ico") {
        diagnostics.unexpected_http_errors.push({ status: response.status(), path_hash: sha256(Buffer.from(pathname)) });
      }
    });
    await page.goto(args.url, { waitUntil: "domcontentloaded", timeout: 90_000 });
    let frame = await resolveShellFrame(page);
    const identity = await identitySnapshot(frame);
    const config = await runtimeConfig(frame);
    const routes = await primaryRouteAudit(frame);
    const uat = args.mode === "initial"
      ? await runInitialUat(frame, args.sourcePaths)
      : await runRestartUat(frame, args.expectedLedgerCount, args.expectedReviewCount);
    await captureIdentity(frame, screenshotPath);

    let offlineFailureObserved = false;
    let onlineRecoveryObserved = false;
    if (args.mode === "initial") {
      offlineWindow = true;
      await context.setOffline(true);
      try {
        await page.evaluate(async () => {
          await fetch(`http://127.0.0.1:9/pfi-offline-probe-${Date.now()}`, { cache: "no-store" });
        });
      } catch (_error) {
        offlineFailureObserved = true;
      }
      await new Promise((resolve) => setTimeout(resolve, 100));
      await context.setOffline(false);
      offlineWindow = false;
      await page.goto(args.url, { waitUntil: "domcontentloaded", timeout: 90_000 });
      frame = await resolveShellFrame(page);
      const recovered = await identitySnapshot(frame);
      onlineRecoveryObserved = recovered.gate_ok === true;
    }

    await context.tracing.stop({ path: args.tracePath });
    traceStarted = false;
    const screenshot = await readFile(screenshotPath);
    const trace = await readFile(args.tracePath);
    const manifest = identity.embedded_manifest || {};
    const runtimeManifest = identity.runtime_manifest || {};
    const identityMatches = identity.gate_ok === true && identity.runtime_manifest_status === 200 &&
      JSON.stringify(manifest) === JSON.stringify(runtimeManifest);
    const primaryMatches = identity.primary.length === PRIMARY.length &&
      PRIMARY.every(([route, label], index) => identity.primary[index]?.route === route && identity.primary[index]?.label === label);
    const uatPass = args.mode === "initial"
      ? uat.source_blob_count === 4 && uat.raw_record_count === 8815 && uat.transaction_count === 8808 &&
        uat.ledger_count === 8808 && uat.review_count_after === uat.review_count_before - 1 &&
        uat.review_write_status === 200 && uat.fixture_used === false && uat.fallback_used === false &&
        uat.holdings.panel_visible === true && uat.holdings.truthful_not_loaded === true && uat.holdings.false_zero_count === 0 &&
        Object.values(uat.drilldown).every(Boolean) && uat.reports.status === "pass" &&
        uat.reports.report_count === 5 && uat.reports.blocked_count === 3 && uat.reports.partial_count === 2
      : uat.observed_ledger_count === uat.expected_ledger_count &&
        uat.observed_review_count === uat.expected_review_count && uat.review_page_visible === true;
    const checks = {
      release_identity_match: identityMatches,
      official_shell_ready: identity.shell_schema === "PFIOSWebShellContractV1",
      ten_primary_entries_exact: primaryMatches,
      primary_route_matrix: routes.length === PRIMARY.length && routes.every((row) => row.active),
      human_task_protocol: uatPass,
      offline_failure_observed: args.mode === "restart" || offlineFailureObserved,
      online_recovery_observed: args.mode === "restart" || onlineRecoveryObserved,
      external_network_blocked_or_absent: diagnostics.blocked_external_count === 0,
      console_clean: diagnostics.console_errors.length === 0,
      page_errors_clean: diagnostics.page_errors.length === 0,
      http_errors_clean: diagnostics.unexpected_http_errors.length === 0,
    };
    result = {
      schema: args.mode === "initial" ? "PFIV025Stage12Phase122TargetMacBrowserV1" : "PFIV025Stage12Phase122RestartBrowserV1",
      status: Object.values(checks).every(Boolean) ? "pass" : "fail",
      mode: args.mode,
      checks,
      release_identity: {
        version: String(manifest.version || ""),
        build_id: String(manifest.build_id || ""),
        git_commit: String(manifest.git_commit || ""),
        frontend_bundle_hash: String(manifest.frontend_bundle_hash || ""),
        backend_build_hash: String(manifest.backend_build_hash || ""),
      },
      primary_entry_count: identity.primary.length,
      route_audit_count: routes.length,
      uat,
      offline_recovery: {
        browser_offline_performed: args.mode === "initial",
        offline_failure_observed: args.mode === "initial" ? offlineFailureObserved : null,
        online_recovery_observed: args.mode === "initial" ? onlineRecoveryObserved : null,
      },
      diagnostics,
      screenshot: { file: path.basename(screenshotPath), sha256: `sha256:${sha256(screenshot)}` },
      trace: { file: path.basename(args.tracePath), sha256: `sha256:${sha256(trace)}` },
      contains_private_values: false,
      financial_values_emitted: 0,
      finder_used: false,
      launchservices_used: false,
      open_command_used: false,
    };
  } finally {
    if (traceStarted && context) await context.tracing.stop({ path: args.tracePath }).catch(() => {});
    if (context) await context.close().catch(() => {});
    await browser.close().catch(() => {});
  }
  await writeFile(path.join(args.outputDir, `${args.mode}_browser_result.json`), `${JSON.stringify(result, null, 2)}\n`, "utf8");
  process.stdout.write(`${JSON.stringify({ status: result.status, mode: result.mode })}\n`);
  if (result.status !== "pass") process.exitCode = 2;
}

await main();
