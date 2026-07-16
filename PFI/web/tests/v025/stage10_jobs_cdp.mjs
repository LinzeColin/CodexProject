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
const outputDir = path.resolve(String(args["output-dir"] || ""));
const rawTrace = path.resolve(String(args["raw-trace"] || ""));
const retryingJobId = String(args["retrying-job-id"] || "");
const deadLetterJobId = String(args["dead-letter-job-id"] || "");
const chromePath = path.resolve(String(args.chrome || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"));
const moduleDir = process.env.PFI_PLAYWRIGHT_MODULE_DIR;
if (!baseUrl || !apiUrl || !apiToken || !outputDir || !rawTrace || !moduleDir || !retryingJobId || !deadLetterJobId) {
  throw new Error("base URL, API URL, API token, output directory, raw trace, state fixtures and cached Playwright module are required");
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
  ), null, { timeout: 20_000 });
}


async function waitForApiTerminal(jobId) {
  const deadline = Date.now() + 25_000;
  while (Date.now() < deadline) {
    const payload = await apiJson(`/api/jobs/${jobId}`);
    if (["succeeded", "failed", "cancelled", "dead_letter"].includes(payload.job?.status)) return payload;
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error("durable job did not reach a terminal state after recovery");
}


async function projectTimelineItem(page, jobId) {
  return page.evaluate((id) => {
    const item = document.querySelector(`[data-stage8-job-id="${id}"]`);
    const progress = item?.querySelector("progress");
    return {
      state: item?.dataset.stage8JobState || "",
      backendState: item?.dataset.stage10BackendState || "",
      source: item?.dataset.stage10JobSource || "",
      fallback: item?.dataset.stage10CacheFallback || "",
      text: item?.textContent || "",
      errorText: item?.querySelector("[data-stage10-job-error]")?.textContent || "",
      resultText: item?.querySelector("[data-stage10-job-result]")?.textContent || "",
      completedUnits: Number(progress?.value || -1),
      totalUnits: Number(progress?.max || -1),
    };
  }, jobId);
}


const diagnostics = {
  consoleErrors: [], pageErrors: [], httpErrors: [], blockedExternal: [],
  requestedOrigins: new Set(), jobRequests: [],
};
const browser = await chromium.launch({ executablePath: chromePath, headless: true, args: browserArgs() });
let result;
try {
  await mkdir(outputDir, { recursive: true });
  const context = await browser.newContext({
    locale: "zh-CN",
    serviceWorkers: "block",
    viewport: { width: 1440, height: 1050 },
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
    diagnostics.blockedExternal.push(requestUrl);
    await route.abort("blockedbyclient");
  });
  await context.tracing.start({ screenshots: false, snapshots: false, sources: false });
  const page = await context.newPage();
  page.on("console", (message) => {
    if (message.type() === "error") diagnostics.consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => diagnostics.pageErrors.push(String(error?.message || error)));
  page.on("response", (response) => {
    if (response.status() >= 400) diagnostics.httpErrors.push({ status: response.status(), url: response.url() });
  });
  page.on("request", (request) => {
    if (request.url().startsWith(`${apiUrl}/api/jobs`)) {
      diagnostics.jobRequests.push({ method: request.method(), path: new URL(request.url()).pathname });
    }
  });

  await page.goto(`${baseUrl}/overview`, { waitUntil: "domcontentloaded" });
  await waitForShell(page);
  await page.waitForSelector(`[data-stage8-job-id="${retryingJobId}"]`, { state: "attached" });
  await page.waitForSelector(`[data-stage8-job-id="${deadLetterJobId}"]`, { state: "attached" });
  const fixtureProjection = {
    retrying: await projectTimelineItem(page, retryingJobId),
    dead_letter: await projectTimelineItem(page, deadLetterJobId),
  };
  await page.locator("[data-run-refresh]:visible").first().click();
  await page.waitForFunction(() => (
    document.body.dataset.pfiStage10JobStatus === "running"
    && Boolean(document.body.dataset.pfiStage10JobId)
  ), null, { timeout: 10_000 });
  const jobId = await page.evaluate(() => document.body.dataset.pfiStage10JobId);
  const runningSnapshot = await apiJson(`/api/jobs/${jobId}`);

  await page.goto(`${baseUrl}/settings`, { waitUntil: "domcontentloaded" });
  await waitForShell(page);
  await page.waitForSelector(
    `[data-stage8-job-id="${jobId}"][data-stage10-job-source="durable_job_api"]`,
    { state: "attached" },
  );
  const restoredBeforeLeaseRecovery = await page.evaluate((id) => ({
    status: document.body.dataset.pfiStage10JobStatus,
    revision: document.body.dataset.pfiStage10JobRevision,
    traceId: document.body.dataset.pfiStage10JobTraceId,
    timelineState: document.querySelector(`[data-stage8-job-id="${id}"]`)?.dataset.stage8JobState || "",
  }), jobId);

  const leavePageStartedAt = Date.now();
  await page.waitForTimeout(10_500);
  const leavePageElapsedMs = Date.now() - leavePageStartedAt;
  const settled = await waitForApiTerminal(jobId);
  await page.reload({ waitUntil: "domcontentloaded" });
  await waitForShell(page);
  await page.waitForFunction((id) => (
    document.body.dataset.pfiStage10JobStatus === "succeeded"
    && document.querySelector(`[data-stage8-job-id="${id}"]`)?.dataset.stage8JobState === "succeeded"
  ), jobId, { timeout: 10_000 });

  const browserProjection = await page.evaluate((id) => {
    const item = document.querySelector(`[data-stage8-job-id="${id}"]`);
    const progress = item?.querySelector("progress");
    return {
      jobId: document.body.dataset.pfiStage10JobId,
      status: document.body.dataset.pfiStage10JobStatus,
      revision: Number(document.body.dataset.pfiStage10JobRevision || -1),
      traceId: document.body.dataset.pfiStage10JobTraceId,
      progressSource: document.body.dataset.pfiStage10JobProgressSource,
      timerBased: document.body.dataset.pfiStage10JobTimerBased,
      externalNetworkCalls: Number(document.body.dataset.pfiStage10JobExternalNetworkCalls || -1),
      timelineState: item?.dataset.stage8JobState || "",
      backendState: item?.dataset.stage10BackendState || "",
      timelineSource: item?.dataset.stage10JobSource || "",
      completedUnits: Number(progress?.value || -1),
      totalUnits: Number(progress?.max || -1),
      meta: item?.querySelector("small")?.textContent || "",
      resultText: item?.querySelector("[data-stage10-job-result]")?.textContent || "",
      taskPhase: document.querySelector("#task-phase")?.textContent || "",
      jobLabel: document.querySelector("#background-job-label")?.textContent || "",
    };
  }, jobId);
  await page.screenshot({ path: path.join(outputDir, "job_recovery_redacted.png"), fullPage: true });

  await page.goto(`${baseUrl}/overview`, { waitUntil: "domcontentloaded" });
  await waitForShell(page);
  await page.locator("[data-run-refresh]:visible").first().click();
  await page.waitForFunction((priorJobId) => (
    Boolean(document.body.dataset.pfiStage10JobId)
    && document.body.dataset.pfiStage10JobId !== priorJobId
    && ["running", "failed"].includes(document.body.dataset.pfiStage10JobStatus)
  ), jobId, { timeout: 10_000 });
  const failureJobId = await page.evaluate(() => document.body.dataset.pfiStage10JobId);
  await page.waitForFunction((id) => (
    document.body.dataset.pfiStage10JobId === id
    && document.body.dataset.pfiStage10JobStatus === "failed"
    && document.querySelector(`[data-stage8-job-id="${id}"]`)?.dataset.stage8JobState === "failed"
  ), failureJobId, { timeout: 10_000 });
  const failureSettled = await apiJson(`/api/jobs/${failureJobId}`);
  const failureProjection = await page.evaluate((id) => {
    const item = document.querySelector(`[data-stage8-job-id="${id}"]`);
    const errorBanner = document.querySelector("[data-error-banner]");
    return {
      state: item?.dataset.stage8JobState || "",
      backendState: item?.dataset.stage10BackendState || "",
      source: item?.dataset.stage10JobSource || "",
      fallback: item?.dataset.stage10CacheFallback || "",
      errorText: item?.querySelector("[data-stage10-job-error]")?.textContent || "",
      resultText: item?.querySelector("[data-stage10-job-result]")?.textContent || "",
      taskPhase: document.querySelector("#task-phase")?.textContent || "",
      taskPhaseState: document.querySelector("#task-phase")?.dataset.progressState || "",
      jobLabelState: document.querySelector("#background-job-label")?.dataset.progressState || "",
      errorBannerVisible: Boolean(errorBanner && !errorBanner.hidden),
      text: item?.textContent || "",
    };
  }, failureJobId);
  await page.screenshot({ path: path.join(outputDir, "job_failure_redacted.png"), fullPage: true });

  const domSnapshot = await page.evaluate((ids) => ({
    schema: "PFIV025Stage10WholeReviewDOMSnapshotV1",
    route: location.pathname,
    bodyJobId: document.body.dataset.pfiStage10JobId || "",
    bodyJobStatus: document.body.dataset.pfiStage10JobStatus || "",
    taskPhase: document.querySelector("#task-phase")?.textContent || "",
    errorBanner: document.querySelector("[data-error-banner]")?.textContent || "",
    timeline: ids.map((id) => {
      const item = document.querySelector(`[data-stage8-job-id="${id}"]`);
      return {
        id,
        state: item?.dataset.stage8JobState || "",
        backendState: item?.dataset.stage10BackendState || "",
        source: item?.dataset.stage10JobSource || "",
        text: item?.textContent || "",
      };
    }),
  }), [retryingJobId, deadLetterJobId, jobId, failureJobId]);
  await writeFile(path.join(outputDir, "dom_snapshot.json"), `${JSON.stringify(domSnapshot, null, 2)}\n`, "utf8");

  const cdp = await context.newCDPSession(page);
  await cdp.send("Accessibility.enable");
  const fullAxTree = await cdp.send("Accessibility.getFullAXTree");
  const relevantNames = ["后台任务", "缓存切片", "失败", "错误", "重试", "结果入口", "死信"];
  const accessibilityTree = {
    schema: "PFIV025Stage10WholeReviewAccessibilityTreeV1",
    nodes: (fullAxTree.nodes || []).map((node) => ({
      role: String(node.role?.value || ""),
      name: String(node.name?.value || ""),
      ignored: node.ignored === true,
    })).filter((node) => !node.ignored && relevantNames.some((value) => node.name.includes(value))),
  };
  await writeFile(path.join(outputDir, "accessibility_tree.json"), `${JSON.stringify(accessibilityTree, null, 2)}\n`, "utf8");
  await context.tracing.stop({ path: rawTrace });
  await context.close();

  const dbJob = settled.job;
  const checks = {
    initial_job_was_running: runningSnapshot.job?.status === "running",
    left_page_and_restored_same_job: restoredBeforeLeaseRecovery.traceId === runningSnapshot.job?.trace?.trace_id,
    left_page_over_ten_seconds: leavePageElapsedMs >= 10_000,
    healthy_long_task_single_attempt: dbJob?.status === "succeeded"
      && Number(dbJob?.attempt_count || 0) === 1
      && (settled.events || []).filter((event) => event.event_type === "heartbeat").length >= 2
      && !(settled.events || []).some((event) => event.event_type === "lease_expired_requeued"),
    ui_status_matches_db: browserProjection.status === dbJob?.status,
    ui_exact_backend_state: browserProjection.timelineState === dbJob?.status
      && browserProjection.backendState === dbJob?.status,
    ui_revision_matches_db: browserProjection.revision === Number(dbJob?.revision),
    ui_trace_matches_db: browserProjection.traceId === dbJob?.trace?.trace_id,
    ui_progress_matches_db: browserProjection.completedUnits === Number(dbJob?.progress?.completed_units)
      && browserProjection.totalUnits === Number(dbJob?.progress?.total_units),
    ui_uses_durable_api: browserProjection.progressSource === "durable_job_api"
      && browserProjection.timelineSource === "durable_job_api",
    ui_is_not_timer_progress: browserProjection.timerBased === "false"
      && dbJob?.progress?.timer_based === false,
    trace_and_retry_visible: browserProjection.meta.includes(dbJob?.trace?.trace_id)
      && browserProjection.meta.includes(`重试 ${dbJob?.observability?.retry_count || 0} 次`),
    result_entry_visible: browserProjection.resultText.includes(dbJob?.result?.artifact_uri || "missing"),
    persisted_retrying_state_visible: fixtureProjection.retrying.state === "retrying"
      && fixtureProjection.retrying.backendState === "retrying"
      && fixtureProjection.retrying.text.includes("等待重试"),
    persisted_dead_letter_state_visible: fixtureProjection.dead_letter.state === "dead_letter"
      && fixtureProjection.dead_letter.backendState === "dead_letter"
      && fixtureProjection.dead_letter.text.includes("死信"),
    explicit_failure_matches_db: failureSettled.job?.status === "failed"
      && failureProjection.state === "failed"
      && failureProjection.backendState === "failed"
      && failureProjection.source === "durable_job_api",
    failure_reason_retry_and_fallback_visible: failureProjection.errorText.includes("CACHE_REFRESH_ERROR")
      && failureProjection.text.includes("重试 0 次")
      && failureProjection.fallback === "true",
    failure_never_presented_as_success: failureProjection.taskPhaseState === "failure"
      && failureProjection.jobLabelState === "failure"
      && failureProjection.errorBannerVisible
      && failureProjection.resultText === "",
    structured_dom_snapshot_present: domSnapshot.timeline.length === 4
      && domSnapshot.bodyJobStatus === "failed",
    accessibility_tree_present: accessibilityTree.nodes.length > 0,
    external_network_zero: diagnostics.blockedExternal.length === 0
      && browserProjection.externalNetworkCalls === 0
      && settled.external_network_calls === 0,
    browser_clean: diagnostics.consoleErrors.length === 0
      && diagnostics.pageErrors.length === 0
      && diagnostics.httpErrors.length === 0,
  };
  result = {
    schema: "PFIV025Stage10WholeReviewBrowserValidationV1",
    status: Object.values(checks).every(Boolean) ? "pass" : "fail",
    checks,
    job_id: jobId,
    failure_job_id: failureJobId,
    database_projection: {
      status: dbJob.status,
      revision: dbJob.revision,
      attempt_count: dbJob.attempt_count,
      completed_units: dbJob.progress?.completed_units,
      total_units: dbJob.progress?.total_units,
      trace_id: dbJob.trace?.trace_id,
      span_id: dbJob.trace?.span_id,
      retry_count: dbJob.observability?.retry_count,
      external_network_calls: dbJob.observability?.external_network_calls,
      structured_log_count: dbJob.observability?.structured_log_count,
    },
    browser_projection: browserProjection,
    failure_database_projection: {
      status: failureSettled.job?.status,
      revision: failureSettled.job?.revision,
      error_code: failureSettled.job?.error?.code,
      cache_fallback_used: failureSettled.job?.observability?.cache_fallback_used,
    },
    failure_browser_projection: failureProjection,
    fixture_projection: fixtureProjection,
    restored_before_lease_recovery: restoredBeforeLeaseRecovery,
    leave_page_elapsed_ms: leavePageElapsedMs,
    event_types: (settled.events || []).map((event) => event.event_type),
    structured_log_count: (settled.logs || []).length,
    requested_origins: [...diagnostics.requestedOrigins].sort(),
    blocked_external_requests: diagnostics.blockedExternal,
    job_requests: diagnostics.jobRequests,
    diagnostics: {
      console_errors: diagnostics.consoleErrors,
      page_errors: diagnostics.pageErrors,
      http_errors: diagnostics.httpErrors,
    },
    finder_used: false,
    launchservices_used: false,
    gui_file_operations_used: false,
  };
  await writeFile(path.join(outputDir, "browser_validation.json"), `${JSON.stringify(result, null, 2)}\n`, "utf8");
  if (result.status !== "pass") throw new Error(`Stage 10 browser checks failed: ${JSON.stringify(checks)}`);
} finally {
  await browser.close();
}
