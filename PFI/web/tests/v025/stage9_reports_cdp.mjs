#!/usr/bin/env node
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

await mkdir(outputDir, { recursive: true });
const diagnostics = {
  consoleErrors: [], pageErrors: [], httpErrors: [], blockedExternal: [], requestedOrigins: new Set(),
};
const { server, baseUrl } = await startServer();
const browser = await chromium.launch({ executablePath: chromePath, headless: true, args: browserArgs() });
let result;
try {
  const context = await browser.newContext({
    locale: "zh-CN",
    serviceWorkers: "block",
    viewport: { width: 1440, height: 1200 },
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
  await context.tracing.start({ screenshots: false, snapshots: false, sources: false });
  const page = await context.newPage();
  page.on("console", (message) => { if (message.type() === "error") diagnostics.consoleErrors.push(message.text()); });
  page.on("pageerror", (error) => diagnostics.pageErrors.push(String(error?.message || error)));
  page.on("response", (response) => {
    if (response.status() >= 400) diagnostics.httpErrors.push({ status: response.status(), url: response.url() });
  });
  await page.goto(`${baseUrl}/reports`, { waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => (
    document.querySelector(".app-shell")?.hidden === false
    && document.body.dataset.pfiReleaseIdentityState === "ready"
    && document.body.dataset.v025Stage9Phase92 === "ready"
    && window.PFI_V025_STAGE9_ANALYSIS?.buildPhase92ViewModel()?.validation?.status === "pass"
  ), null, { timeout: 30_000 });
  await page.waitForTimeout(250);

  const visible = await page.evaluate(() => {
    const cardRows = [...document.querySelectorAll("[data-home-card]")]
      .filter((item) => !item.hidden)
      .map((item) => ({
        label: item.querySelector("span")?.textContent || "",
        value: item.querySelector("[data-card-value]")?.textContent || "",
        detail: item.querySelector("[data-card-detail]")?.textContent || "",
      }));
    const workflowCards = [...document.querySelectorAll(".workflow-card")].map((item) => ({
      text: item.textContent || "",
      route: item.querySelector("button[data-route-alias]")?.getAttribute("data-route-alias") || "",
    }));
    const bodyText = document.querySelector("#main-workspace")?.textContent || "";
    return {
      phaseAttribute: document.body.dataset.v025Stage9Phase92 || "",
      routeAlias: document.querySelector("#main-workspace")?.dataset.routeAlias || "",
      title: document.querySelector("#workspace-title")?.textContent || "",
      kicker: document.querySelector("#workspace-kicker")?.textContent || "",
      cardRows,
      workflowCards,
      bodyText,
      viewValidation: window.PFI_V025_STAGE9_ANALYSIS.validatePhase92ViewModel(),
    };
  });
  const requiredText = [
    "净资产报告", "现金报告", "投资报告", "消费报告", "现金流报告",
    "FORM-PFI-015", "FORM-PFI-020", "现金流窗口敏感性", "模型验证卡",
    "来源复核", "缺失输入不解释为零", "Phase 9.3",
  ];
  const missingRequiredText = requiredText.filter((text) => !visible.bodyText.includes(text));
  const checks = {
    phase_contract_ready: visible.phaseAttribute === "ready" && visible.viewValidation.status === "pass",
    reports_route_mounted: visible.routeAlias.startsWith("/reports") && visible.title.startsWith("报告与洞察"),
    five_report_cards_visible: visible.cardRows.length === 5,
    report_truth_statuses_visible: visible.cardRows.filter((item) => item.value === "已阻断").length === 3
      && visible.cardRows.filter((item) => item.value === "部分可算").length === 2,
    all_analysis_sections_visible: missingRequiredText.length === 0,
    actionable_routes_present: visible.workflowCards.length === 23
      && visible.workflowCards.every((item) => item.route.startsWith("/")),
    no_financial_amount_visible: !/\bCNY\s+-?[0-9]/.test(visible.bodyText),
    no_false_complete_conclusion: !visible.bodyText.includes("完整财务结论"),
    no_phase93_or_trade_execution: visible.bodyText.includes("尚未开始")
      && !visible.bodyText.includes("自动交易已启用"),
    no_browser_errors: diagnostics.consoleErrors.length === 0
      && diagnostics.pageErrors.length === 0
      && diagnostics.httpErrors.length === 0,
    loopback_only: diagnostics.blockedExternal.length === 0
      && diagnostics.requestedOrigins.size === 1
      && diagnostics.requestedOrigins.has(allowedOrigin),
  };
  const sensitivityCard = page.locator(".workflow-card").filter({ hasText: "现金流窗口敏感性" }).first();
  await sensitivityCard.scrollIntoViewIfNeeded();
  await page.waitForTimeout(100);
  await page.screenshot({ path: path.join(outputDir, "sensitivity_view.png"), fullPage: false });
  await context.tracing.stop({ path: rawTrace });
  result = {
    schema: "PFIV025Stage9Phase92BrowserResultV1",
    status: Object.values(checks).every(Boolean) ? "pass" : "fail",
    checks,
    checkCount: Object.keys(checks).length,
    passedCheckCount: Object.values(checks).filter(Boolean).length,
    visible: {
      phaseAttribute: visible.phaseAttribute,
      routeAlias: visible.routeAlias,
      title: visible.title,
      kicker: visible.kicker,
      reportCards: visible.cardRows,
      workflowCardCount: visible.workflowCards.length,
      missingRequiredText,
    },
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
  };
  await writeFile(path.join(outputDir, "playwright_result.json"), `${JSON.stringify(result, null, 2)}\n`, "utf8");
  await context.close();
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
}
if (result?.status !== "pass") {
  throw new Error(`Stage 9 Phase 9.2 browser validation failed: ${JSON.stringify(result)}`);
}
console.log(`stage9 phase 9.2 browser: ${result.passedCheckCount}/${result.checkCount} pass`);
