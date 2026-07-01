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
const PHASE71_DIR = path.join(ROOT, "reports", "pfi_v024", "stage_7", "phase_7_1");
const PHASE73_DIR = path.join(ROOT, "reports", "pfi_v024", "stage_7", "phase_7_3");
const REPORT_SCHEMA_PATH = path.join(PHASE71_DIR, "report_schema.json");
const FORMULA_SCREENSHOT_PATH = path.join(PHASE73_DIR, "formula_visibility.png");
const PLAYWRIGHT_PACKAGE_PATH = process.env.PLAYWRIGHT_PACKAGE_PATH || "";
const REQUIRED_REPORT_NAMES = Object.freeze(["净资产报告", "现金报告", "投资报告", "消费报告", "现金流报告", "数据质量报告"]);
const REQUIRED_VISIBLE_TERMS = Object.freeze(["结论", "公式", "参数", "样本量", "数据范围", "置信度", "缺口", "复核入口"]);
const serverNotFoundPaths = [];

function ensureDirs() {
  fs.mkdirSync(PHASE73_DIR, { recursive: true });
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf-8"));
}

function writeJson(filePath, payload) {
  fs.writeFileSync(filePath, `${JSON.stringify(payload, null, 2)}\n`);
}

function relativePath(filePath) {
  return path.relative(REPO_ROOT, filePath).split(path.sep).join("/");
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

function escapeScriptJson(payload) {
  return JSON.stringify(payload).replace(/<\//g, "<\\/");
}

function buildIndexHtml(reportPack) {
  const indexPath = path.join(WEB_ROOT, "index.html");
  const base = fs.readFileSync(indexPath, "utf-8");
  const injected = `<script type="application/json" id="pfi-stage7-report-schema">${escapeScriptJson(reportPack)}</script>`;
  const pattern = /<script\b[^>]*id=["']pfi-stage7-report-schema["'][^>]*>[\s\S]*?<\/script>/;
  if (pattern.test(base)) return base.replace(pattern, injected);
  return base.replace("</body>", `${injected}\n</body>`);
}

function startStaticServer(reportPack) {
  const indexHtml = buildIndexHtml(reportPack);
  const emptyRuntimePayload = JSON.stringify({
    status: "not_mounted_static_validation",
    trends: {},
    readModel: {},
  });
  const server = http.createServer((request, response) => {
    try {
      const requestUrl = new URL(request.url || "/", "http://127.0.0.1");
      if (requestUrl.pathname === "/favicon.ico") {
        response.writeHead(204);
        response.end();
        return;
      }
      if (requestUrl.pathname === "/api/trends" || requestUrl.pathname === "/api/read-model" || requestUrl.pathname === "/api/read-model-status") {
        response.writeHead(200, { "Content-Type": "application/json; charset=utf-8" });
        response.end(emptyRuntimePayload);
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

function buildDataQualityReportHtml(viewModel) {
  const qualityReport = viewModel.report_cards.find((card) => card.report_id === "data_quality_report");
  if (!qualityReport) throw new Error("data_quality_report is required");
  const gapItems = qualityReport.gaps.map((gap) => `<li><strong>${gap.metric_id}</strong>: ${gap.reason_zh}</li>`).join("\n");
  const sources = qualityReport.metric_sources.map((source) => `<li>${source}</li>`).join("\n");
  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>PFI v0.2.4 Stage 7 Phase 7.3 数据质量报告</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #172033; background: #f7f8fb; margin: 0; padding: 32px; }
    main { max-width: 960px; margin: 0 auto; background: #fff; border: 1px solid #d9dee8; border-radius: 8px; padding: 28px; }
    h1 { margin: 0 0 8px; font-size: 24px; }
    h2 { margin-top: 24px; font-size: 16px; }
    p, li { line-height: 1.6; }
    .meta { color: #526070; }
    .status { display: inline-block; padding: 4px 8px; border-radius: 4px; background: #e8f4ed; color: #17623b; font-weight: 600; }
    code { background: #eef1f5; padding: 2px 4px; border-radius: 4px; }
  </style>
</head>
<body>
  <main>
    <h1>${qualityReport.title_zh}</h1>
    <p class="meta">来源：真实 Stage 4 read model / MetaDatabase/PFI；不写入、不补造、不改写财务数据。</p>
    <p><span class="status">${qualityReport.status_zh}</span></p>
    <h2>结论</h2>
    <p>${qualityReport.conclusion_zh}</p>
    <h2>公式</h2>
    <p>${qualityReport.formula_zh}</p>
    <h2>参数与样本量</h2>
    <p>${qualityReport.parameter_summary_zh}</p>
    <p>${qualityReport.sample_size_zh}</p>
    <h2>数据范围与置信度</h2>
    <p>${qualityReport.data_range_zh}</p>
    <p>${qualityReport.confidence_zh}</p>
    <h2>指标来源</h2>
    <ul>${sources}</ul>
    <h2>缺口与复核入口</h2>
    <ul>${gapItems}</ul>
    <p>${qualityReport.review_entry_zh}</p>
  </main>
</body>
</html>
`;
}

function buildChangedFiles() {
  return [
    "PFI/web/app/pages/reports.js",
    "PFI/scripts/validate_v024_stage7_phase73_report_acceptance.js",
    "PFI/tests/test_v024_stage7_phase73_report_acceptance.py",
    "PFI/docs/pfi_v024/STAGE7_REPORT_ANALYSIS.md",
    "PFI/docs/pfi_v024/RUN_CONTRACT.md",
    "PFI/reports/pfi_v024/stage_7/phase_7_3/evidence.json",
    "PFI/reports/pfi_v024/stage_7/phase_7_3/report_acceptance_gate.json",
    "PFI/reports/pfi_v024/stage_7/phase_7_3/browser_validation.json",
    "PFI/reports/pfi_v024/stage_7/phase_7_3/sample_data_quality_report.html",
    "PFI/reports/pfi_v024/stage_7/phase_7_3/formula_visibility.png",
    "PFI/reports/pfi_v024/stage_7/phase_7_3/changed_files.txt",
    "PFI/reports/pfi_v024/stage_7/phase_7_3/terminal.log",
    "PFI/reports/pfi_v024/stage_7/phase_7_3/risk_and_rollback.md",
    "PFI/README.md",
    "PFI/HANDOFF.md",
    "PFI/CHANGELOG.md",
    "PFI/功能清单.md",
    "PFI/开发记录.md",
    "PFI/模型参数文件.md",
  ];
}

async function main() {
  ensureDirs();
  const reportsPage = require(path.join(ROOT, "web", "app", "pages", "reports.js"));
  const reportPack = readJson(REPORT_SCHEMA_PATH);
  const contract = reportsPage.buildV024Stage7Phase73Contract();
  const viewModel = reportsPage.buildV024Stage7Phase72ReportCenterViewModel(reportPack);
  const acceptanceGate = reportsPage.validateV024Stage7Phase73Acceptance(viewModel);
  const qualityHtml = buildDataQualityReportHtml(viewModel);
  const changedFiles = buildChangedFiles();

  writeJson(path.join(PHASE73_DIR, "report_acceptance_gate.json"), acceptanceGate);
  fs.writeFileSync(path.join(PHASE73_DIR, "sample_data_quality_report.html"), qualityHtml);
  fs.writeFileSync(path.join(PHASE73_DIR, "changed_files.txt"), `${changedFiles.join("\n")}\n`);

  const { server, baseUrl } = await startStaticServer(reportPack);
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

    await page.goto(`${baseUrl}/index.html#${encodeURIComponent("/reports?tab=data-quality")}`, { waitUntil: "networkidle" });
    await page.waitForFunction(() => {
      return document.querySelector(".app-shell")?.dataset.state === "ready"
        && document.querySelector("#main-workspace")?.dataset.activeWorkspace === "insights";
    });

    const browserState = await page.evaluate(({ requiredReportNames, requiredVisibleTerms }) => {
      const main = document.querySelector("#main-workspace");
      const bodyText = document.body.innerText || "";
      const reportNamesVisible = requiredReportNames.every((term) => bodyText.includes(term));
      const requiredTermsVisible = requiredVisibleTerms.every((term) => bodyText.includes(term));
      const api = window.PFI_V024_STAGE7_REPORTS;
      const reportPackNode = document.querySelector("#pfi-stage7-report-schema");
      const reportPack = JSON.parse(reportPackNode?.textContent || "{}");
      const view = api?.buildV024Stage7Phase72ReportCenterViewModel(reportPack);
      const gate = api?.validateV024Stage7Phase73Acceptance(view);
      return {
        activeWorkspace: main?.dataset.activeWorkspace || "",
        reportNamesVisible,
        requiredTermsVisible,
        containsFullFinancialConclusion: bodyText.includes("完整财务结论"),
        containsZeroFinancialPlaceholder: bodyText.includes("CNY 0.00"),
        reportCount: view?.report_count || 0,
        gateStatus: gate?.status || "",
        bodyTextLength: bodyText.length,
      };
    }, { requiredReportNames: REQUIRED_REPORT_NAMES, requiredVisibleTerms: REQUIRED_VISIBLE_TERMS });

    await page.screenshot({ path: FORMULA_SCREENSHOT_PATH, fullPage: true });
    const screenshotBytes = fs.statSync(FORMULA_SCREENSHOT_PATH).size;

    const validation = {
      schema: "PFIV024Stage7Phase73BrowserValidationV1",
      target_version: "v0.2.4",
      source_package_version: "v0.2.3-repair",
      stage: "Stage 7",
      phase_id: "7.3",
      phase_name: "验收",
      source: `${baseUrl}/index.html#/reports?tab=data-quality`,
      playwright_package_path: PLAYWRIGHT_PACKAGE_PATH,
      status: "pass",
      active_workspace: browserState.activeWorkspace,
      report_count: browserState.reportCount,
      report_names_visible: browserState.reportNamesVisible,
      required_terms_visible: browserState.requiredTermsVisible,
      browser_gate_status: browserState.gateStatus,
      body_text_length: browserState.bodyTextLength,
      contains_full_financial_conclusion: browserState.containsFullFinancialConclusion,
      contains_zero_financial_placeholder: browserState.containsZeroFinancialPlaceholder,
      formula_visibility_screenshot: fs.existsSync(FORMULA_SCREENSHOT_PATH),
      formula_visibility_screenshot_path: relativePath(FORMULA_SCREENSHOT_PATH),
      formula_visibility_screenshot_bytes: screenshotBytes,
      console_errors: consoleErrors,
      page_errors: pageErrors,
      http_errors: httpErrors,
      server_not_found_paths: serverNotFoundPaths,
      generated_at: new Date().toISOString(),
    };

    const failures = [];
    if (acceptanceGate.status !== "pass") failures.push("acceptance gate failed");
    if (browserState.activeWorkspace !== "insights") failures.push(`active workspace=${browserState.activeWorkspace}`);
    if (browserState.reportCount !== 6) failures.push(`report_count=${browserState.reportCount}`);
    if (!browserState.reportNamesVisible) failures.push("report names not visible");
    if (!browserState.requiredTermsVisible) failures.push("required terms not visible");
    if (browserState.gateStatus !== "pass") failures.push(`browser gate=${browserState.gateStatus}`);
    if (browserState.containsFullFinancialConclusion) failures.push("full financial conclusion visible");
    if (browserState.containsZeroFinancialPlaceholder) failures.push("zero placeholder visible");
    if (screenshotBytes <= 10000) failures.push(`screenshot too small=${screenshotBytes}`);
    if (consoleErrors.length || pageErrors.length || httpErrors.length || serverNotFoundPaths.length) failures.push("browser errors present");
    if (failures.length) validation.status = "fail";
    validation.failures = failures;

    writeJson(path.join(PHASE73_DIR, "browser_validation.json"), validation);

    const evidence = {
      schema: "PFIV024Stage7Phase73EvidenceV1",
      target_version: "v0.2.4",
      source_package_version: "v0.2.3-repair",
      stage: "Stage 7",
      phase_id: "7.3",
      phase_name: "验收",
      contract_version: contract.contract_version,
      status: acceptanceGate.status === "pass" && validation.status === "pass" ? "candidate_pass" : "candidate_fail",
      current_phase_only: true,
      max_one_phase_per_run: true,
      phase_7_1_complete_required: true,
      phase_7_2_complete_required: true,
      phase_7_3_acceptance_complete: true,
      stage_7_whole_review_complete: false,
      github_main_uploaded: false,
      app_bundle_reinstall_executed: false,
      data_logic_changes_made: false,
      formal_fake_financial_data_added: false,
      source_report_schema: relativePath(REPORT_SCHEMA_PATH),
      source_read_model_hash: reportPack.read_model_hash,
      source_record_count: reportPack.source?.record_count || 0,
      source_raw_file_count: reportPack.source?.raw_file_count || 0,
      source_date_range: reportPack.source?.date_range || null,
      visible_report_ids: acceptanceGate.visible_report_ids,
      report_acceptance_gate: relativePath(path.join(PHASE73_DIR, "report_acceptance_gate.json")),
      browser_validation: relativePath(path.join(PHASE73_DIR, "browser_validation.json")),
      data_quality_report_html: relativePath(path.join(PHASE73_DIR, "sample_data_quality_report.html")),
      formula_visibility_screenshot: relativePath(FORMULA_SCREENSHOT_PATH),
      changed_files: changedFiles,
      explicitly_not_done: [
        "Stage 7 whole-stage review",
        "GitHub main upload",
        "app bundle reinstall",
        "financial data mutation or synthesis",
      ],
      generated_at: new Date().toISOString(),
      evidence_hash: crypto.createHash("sha256").update(JSON.stringify({
        acceptanceGate,
        browserState,
        screenshotBytes,
        source_read_model_hash: reportPack.read_model_hash,
      })).digest("hex"),
    };
    writeJson(path.join(PHASE73_DIR, "evidence.json"), evidence);

    const log = [
      "PFI v0.2.4 Stage 7 Phase 7.3 acceptance evidence generation",
      `acceptance_gate=${acceptanceGate.status}`,
      `browser_validation=${validation.status}`,
      `formula_visibility_screenshot_bytes=${screenshotBytes}`,
      `source_report_schema=${relativePath(REPORT_SCHEMA_PATH)}`,
      "whole_stage_review=not_executed",
      "github_main_upload=not_executed",
      "app_bundle_reinstall=not_executed",
      "financial_data_mutation=not_executed",
      `failures=${failures.join("; ") || "none"}`,
    ].join("\n");
    fs.writeFileSync(path.join(PHASE73_DIR, "terminal.log"), `${log}\n`);
    fs.writeFileSync(
      path.join(PHASE73_DIR, "risk_and_rollback.md"),
      [
        "# Stage 7 Phase 7.3 Risk And Rollback",
        "",
        "- Scope: acceptance evidence, browser screenshot, and report-center quality gate only.",
        "- No real financial data files were written, cleaned, deleted, synthesized, or backfilled.",
        "- Rollback: revert this phase's changed files and remove `PFI/reports/pfi_v024/stage_7/phase_7_3/` artifacts.",
        "- Stop condition: do not proceed to Stage 7 whole-stage review or GitHub main upload in this run.",
        "",
      ].join("\n"),
    );

    console.log(JSON.stringify({
      status: evidence.status,
      acceptance_gate: acceptanceGate.status,
      browser_validation: validation.status,
      report_count: acceptanceGate.visible_report_ids.length,
      formula_visibility_screenshot_bytes: screenshotBytes,
      phase_dir: PHASE73_DIR,
      failures,
    }, null, 2));
    if (evidence.status !== "candidate_pass") process.exitCode = 1;
  } finally {
    if (browser) await browser.close();
    server.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
