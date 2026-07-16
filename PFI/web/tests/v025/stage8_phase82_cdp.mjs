#!/usr/bin/env node
import { createHash } from "node:crypto";
import { createReadStream } from "node:fs";
import { mkdir, readFile, stat, unlink, writeFile } from "node:fs/promises";
import http from "node:http";
import { createRequire } from "node:module";
import path from "node:path";
import { spawnSync } from "node:child_process";


const require = createRequire(import.meta.url);
const args = Object.fromEntries(process.argv.slice(2).reduce((pairs, value, index, values) => {
  if (value.startsWith("--")) pairs.push([value.slice(2), values[index + 1]]);
  return pairs;
}, []));
const webRoot = path.resolve(String(args["web-root"] || ""));
const outputDir = path.resolve(String(args["output-dir"] || ""));
const chromePath = path.resolve(String(args.chrome || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"));
const moduleDir = process.env.PFI_PLAYWRIGHT_MODULE_DIR;
if (!webRoot || !outputDir || !moduleDir) throw new Error("web root, output directory and cached Playwright module are required");
const { chromium } = require(path.join(moduleDir, "playwright"));

const CONTENT_TYPES = Object.freeze({
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
});

function browserArgs() {
  return [
    "--disable-background-networking", "--disable-component-update", "--disable-default-apps",
    "--disable-domain-reliability", "--disable-extensions",
    "--disable-features=OptimizationHints,MediaRouter,ServiceWorker", "--disable-sync",
    "--disable-gpu", "--metrics-recording-only", "--no-first-run", "--no-default-browser-check",
  ];
}

function jsonResponse(response, statusCode, payload) {
  const body = JSON.stringify(payload);
  response.writeHead(statusCode, {
    "Cache-Control": "no-store",
    "Content-Type": "application/json; charset=utf-8",
    "Content-Length": Buffer.byteLength(body),
  });
  response.end(body);
}

function runtimeConfig(baseUrl) {
  return JSON.stringify({
    apiBaseUrl: baseUrl,
    apiAuthToken: "stage8-phase82-browser-token",
    readModelStatusApi: true,
    runtimeApiEnabled: true,
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
  const relative = nestedAsset || clean;
  const candidate = path.resolve(webRoot, relative);
  return candidate === webRoot || candidate.startsWith(`${webRoot}${path.sep}`) ? candidate : null;
}

async function startServer() {
  let baseUrl = "";
  let trendsDelayMs = 0;
  let settingsDelayMs = 0;
  let settingsFail = false;
  let settingsRevision = 1;
  let preferences = {
    default_account: "主账户",
    theme_language: "中文优先",
    feedback_haptic: false,
    feedback_sound: false,
    feedback_motion: true,
  };
  const server = http.createServer(async (request, response) => {
    try {
      const requestUrl = new URL(request.url || "/", baseUrl || "http://127.0.0.1");
      if (requestUrl.pathname === "/api/trends") {
        if (trendsDelayMs) await new Promise((resolve) => setTimeout(resolve, trendsDelayMs));
        return jsonResponse(response, 200, { trends: {}, readModel: {} });
      }
      if (requestUrl.pathname === "/api/read-model") return jsonResponse(response, 200, {});
      if (requestUrl.pathname === "/api/read-model-status") return jsonResponse(response, 200, {});
      if (requestUrl.pathname === "/api/health") return jsonResponse(response, 200, { status: "ready" });
      if (requestUrl.pathname === "/api/settings/preferences" && request.method === "GET") {
        return jsonResponse(response, 200, { preferences, revision: settingsRevision, persisted: true, updated_at: "2026-07-15T00:00:00Z" });
      }
      if (requestUrl.pathname === "/api/settings/preferences" && request.method === "POST") {
        if (settingsDelayMs) await new Promise((resolve) => setTimeout(resolve, settingsDelayMs));
        if (settingsFail) return jsonResponse(response, 503, { error: "expected delayed settings failure" });
        let body = "";
        for await (const chunk of request) body += chunk;
        const payload = JSON.parse(body || "{}");
        preferences = { ...preferences, ...(payload.preferences || {}) };
        settingsRevision += 1;
        return jsonResponse(response, 200, { preferences, revision: settingsRevision, persisted: true, updated_at: "2026-07-15T00:00:01Z" });
      }

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
      jsonResponse(response, 500, { error: String(error?.message || error) });
    }
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const address = server.address();
  if (!address || typeof address === "string") throw new Error("loopback server address is unavailable");
  baseUrl = `http://127.0.0.1:${address.port}`;
  return {
    server,
    baseUrl,
    setTrendsDelay: (value) => { trendsDelayMs = Number(value) || 0; },
    setSettingsDelay: (value) => { settingsDelayMs = Number(value) || 0; },
    setSettingsFail: (value) => { settingsFail = Boolean(value); },
  };
}

function watchPage(page, diagnostics) {
  page.on("console", (message) => { if (message.type() === "error") diagnostics.consoleErrors.push(message.text()); });
  page.on("pageerror", (error) => diagnostics.pageErrors.push(String(error?.message || error)));
  page.on("response", (response) => {
    if (response.status() >= 400) diagnostics.httpErrors.push({ status: response.status(), url: response.url() });
  });
}

async function routeLoopbackOnly(context, baseUrl, diagnostics) {
  const origin = new URL(baseUrl).origin;
  await context.route("**/*", async (route) => {
    const requestUrl = route.request().url();
    const parsed = new URL(requestUrl);
    if (["data:", "blob:", "about:"].includes(parsed.protocol) || parsed.origin === origin) {
      if (parsed.origin === origin) diagnostics.requestedOrigins.add(parsed.origin);
      await route.continue();
      return;
    }
    diagnostics.blockedExternal.push(requestUrl);
    await route.abort("blockedbyclient");
  });
}

async function waitForReady(page) {
  try {
    await page.waitForFunction(() => (
      document.querySelector(".app-shell")?.hidden === false
      && document.body.dataset.pfiReleaseIdentityState === "ready"
      && Boolean(window.PFI_V025_STAGE8_MOTION)
      && Boolean(window.PFI_V025_STAGE8_HAPTICS)
      && Boolean(window.PFI_V025_STAGE8_JOB_TIMELINE)
    ), null, { timeout: 30_000 });
  } catch (error) {
    const state = await page.evaluate(() => ({
      shellHidden: document.querySelector(".app-shell")?.hidden,
      releaseIdentityState: document.body.dataset.pfiReleaseIdentityState || "missing",
      motionLoaded: Boolean(window.PFI_V025_STAGE8_MOTION),
      hapticsLoaded: Boolean(window.PFI_V025_STAGE8_HAPTICS),
      jobsLoaded: Boolean(window.PFI_V025_STAGE8_JOB_TIMELINE),
      conflict: document.querySelector("[data-pfi-release-conflict-detail]")?.textContent?.trim() || "",
    }));
    throw new Error(`PFI Phase 8.2 ready timeout: ${JSON.stringify(state)}`, { cause: error });
  }
}

async function runNormalMotionScenario(
  browser, baseUrl, diagnostics, tracePath, setTrendsDelay, setSettingsDelay, setSettingsFail,
) {
  const context = await browser.newContext({
    locale: "zh-CN", serviceWorkers: "block", viewport: { width: 1440, height: 1000 }, reducedMotion: "no-preference",
  });
  await context.addInitScript(() => {
    window.__PFI_VIBRATIONS__ = [];
    Object.defineProperty(navigator, "vibrate", {
      configurable: true,
      value: (pattern) => { window.__PFI_VIBRATIONS__.push(pattern); return true; },
    });
  });
  await routeLoopbackOnly(context, baseUrl, diagnostics);
  await context.tracing.start({ screenshots: false, snapshots: false, sources: false });
  const page = await context.newPage();
  watchPage(page, diagnostics);
  await page.goto(`${baseUrl}/settings/feedback`, { waitUntil: "domcontentloaded" });
  await waitForReady(page);
  await page.waitForFunction(() => document.querySelector("[data-settings-save-status]")?.textContent?.includes("SQLite"), null, { timeout: 10_000 });

  const initial = await page.evaluate(() => ({
    motionContract: window.PFI_V025_STAGE8_MOTION.contract,
    hapticsContract: window.PFI_V025_STAGE8_HAPTICS.contract,
    jobsContract: window.PFI_V025_STAGE8_JOB_TIMELINE.contract,
    reduced: window.PFI_V025_STAGE8_MOTION.reducedMotionActive(),
    hapticChecked: document.querySelector('[data-feedback-toggle="haptic"]')?.checked,
    soundChecked: document.querySelector('[data-feedback-toggle="sound"]')?.checked,
    hapticCapability: window.PFI_V025_STAGE8_HAPTICS.capability(),
  }));

  await page.click('[data-feedback-toggle="haptic"]');
  await page.click("[data-feedback-test]");
  const haptic = await page.evaluate(() => ({
    checked: document.querySelector('[data-feedback-toggle="haptic"]')?.checked,
    calls: window.__PFI_VIBRATIONS__.slice(),
    status: document.body.dataset.v025HapticStatus || "",
  }));

  const jobBeforeRoute = await page.evaluate(() => {
    const api = window.PFI_V025_STAGE8_JOB_TIMELINE;
    api.start({ id: "browser-real-job", label: "真实工作量校验", stageLabel: "核对 4 个已知单元", startedAt: Date.now() - 11_000 });
    const noUnits = api.snapshot("browser-real-job");
    api.update("browser-real-job", { completedUnits: 2, totalUnits: 4, stageLabel: "已核对 2/4 个单元" });
    const withUnits = api.snapshot("browser-real-job");
    const entry = document.querySelector('[data-stage8-job-id="browser-real-job"]');
    const progress = entry?.querySelector("progress");
    return {
      noUnits,
      withUnits,
      durable: entry?.dataset.stage8JobDurable || "",
      progressValue: progress?.value,
      progressMax: progress?.max,
      progressText: progress?.getAttribute("aria-valuetext") || "",
    };
  });
  await page.click('[data-primary-entry="true"][data-workspace="accounts"]');
  await page.waitForFunction(() => document.querySelector("#main-workspace")?.dataset.activeWorkspace === "accounts");
  const routeMotion = await page.evaluate(() => ({
    jobStillVisible: Boolean(document.querySelector('[data-stage8-job-id="browser-real-job"]')),
    routeMode: document.body.dataset.v025ViewTransition || "",
    activeAnimations: document.getAnimations().filter((item) => item.playState === "running").length,
  }));

  setTrendsDelay(450);
  await page.click("[data-run-refresh]");
  await page.waitForTimeout(120);
  const beforeSkeleton = await page.evaluate(() => document.querySelector("[data-skeleton]")?.hidden !== false);
  await page.waitForTimeout(240);
  const afterBudget = await page.evaluate(() => ({
    skeletonVisible: document.querySelector("[data-skeleton]")?.hidden === false,
    feedbackState: document.querySelector("[data-action-feedback]")?.dataset.feedbackState || "",
  }));
  await page.waitForFunction(() => document.querySelector("[data-action-feedback]")?.dataset.feedbackState === "success", null, { timeout: 5_000 });
  const refreshComplete = await page.evaluate(() => ({
    skeletonHidden: document.querySelector("[data-skeleton]")?.hidden === true,
    feedbackState: document.querySelector("[data-action-feedback]")?.dataset.feedbackState || "",
  }));
  setTrendsDelay(0);

  await page.goto(`${baseUrl}/settings/account`, { waitUntil: "domcontentloaded" });
  await waitForReady(page);
  await page.evaluate(() => {
    const feedback = document.querySelector("[data-action-feedback]");
    if (feedback) feedback.dataset.feedbackState = "blocked";
  });
  setSettingsDelay(500);
  setSettingsFail(true);
  await page.click("[data-settings-save]");
  await page.waitForTimeout(260);
  const delayedSettingsBeforeResponse = await page.evaluate(() => ({
    feedbackState: document.querySelector("[data-action-feedback]")?.dataset.feedbackState || "",
    feedbackMessage: document.querySelector("[data-action-feedback-message]")?.textContent?.trim() || "",
  }));
  await page.waitForFunction(() => document.querySelector("[data-action-feedback]")?.dataset.feedbackState === "failure", null, { timeout: 5_000 });
  const delayedSettingsFailure = await page.evaluate(() => ({
    feedbackState: document.querySelector("[data-action-feedback]")?.dataset.feedbackState || "",
    feedbackMessage: document.querySelector("[data-action-feedback-message]")?.textContent?.trim() || "",
  }));
  setSettingsDelay(0);
  setSettingsFail(false);

  const screenshotPath = path.join(outputDir, "phase82_motion_feedback.png");
  await page.screenshot({ path: screenshotPath, fullPage: false, animations: "disabled" });
  const screenshotBytes = (await stat(screenshotPath)).size;
  await context.tracing.stop({ path: tracePath });
  await context.close();
  return {
    initial, haptic, jobBeforeRoute, routeMotion, beforeSkeleton, afterBudget, refreshComplete,
    delayedSettingsBeforeResponse, delayedSettingsFailure, screenshotBytes,
  };
}

async function runReducedUnsupportedScenario(browser, baseUrl, diagnostics) {
  const context = await browser.newContext({
    locale: "zh-CN", serviceWorkers: "block", viewport: { width: 390, height: 844 }, reducedMotion: "reduce",
  });
  await context.addInitScript(() => {
    Object.defineProperty(navigator, "vibrate", { configurable: true, value: undefined });
    Object.defineProperty(window, "AudioContext", { configurable: true, value: undefined });
    Object.defineProperty(window, "webkitAudioContext", { configurable: true, value: undefined });
  });
  await routeLoopbackOnly(context, baseUrl, diagnostics);
  const page = await context.newPage();
  watchPage(page, diagnostics);
  await page.goto(`${baseUrl}/overview`, { waitUntil: "domcontentloaded" });
  await waitForReady(page);
  const result = await page.evaluate(() => {
    const main = document.querySelector("#main-workspace");
    const motionResult = window.PFI_V025_STAGE8_MOTION.animateState(main, "enter");
    const unsupportedResult = window.PFI_V025_STAGE8_HAPTICS.emit("confirm");
    return {
      reduced: window.PFI_V025_STAGE8_MOTION.reducedMotionActive(),
      motionDuration: motionResult.duration,
      capability: window.PFI_V025_STAGE8_HAPTICS.capability(),
      unsupportedResult,
      activeAnimations: document.getAnimations().filter((item) => item.playState === "running").length,
      elapsedClasses: [80, 250, 350, 1500, 11000].map(window.PFI_V025_STAGE8_MOTION.classifyElapsed),
    };
  });
  await context.close();
  return result;
}

await mkdir(outputDir, { recursive: true });
const rawTracePath = path.join(outputDir, ".browser_trace_raw.zip");
const tracePath = path.join(outputDir, "browser_trace.zip");
const diagnostics = { consoleErrors: [], pageErrors: [], httpErrors: [], blockedExternal: [], requestedOrigins: new Set() };
const { server, baseUrl, setTrendsDelay, setSettingsDelay, setSettingsFail } = await startServer();
const browser = await chromium.launch({ executablePath: chromePath, headless: true, args: browserArgs() });
let result;
try {
  const normal = await runNormalMotionScenario(
    browser, baseUrl, diagnostics, rawTracePath, setTrendsDelay, setSettingsDelay, setSettingsFail,
  );
  const reduced = await runReducedUnsupportedScenario(browser, baseUrl, diagnostics);
  const checks = {
    feedback_budget_contract: JSON.stringify(normal.initial.motionContract.feedbackBudgetMs) === JSON.stringify({ instant: 100, cached: 300, staged: 1000, durable: 10000 }),
    normal_motion_bounded: normal.initial.reduced === false && normal.initial.motionContract.maxMotionMs === 220,
    progressive_route_transition: ["view_transition", "css_fallback"].includes(normal.routeMotion.routeMode),
    haptics_sound_default_off: normal.initial.hapticChecked === false && normal.initial.soundChecked === false,
    haptic_explicit_opt_in: normal.haptic.checked === true && normal.haptic.calls.length >= 1,
    actual_units_only_progress: normal.jobBeforeRoute.noUnits.actualProgress === null
      && normal.jobBeforeRoute.withUnits.actualProgress === 0.5
      && normal.jobBeforeRoute.progressValue === 2
      && normal.jobBeforeRoute.progressMax === 4
      && normal.jobBeforeRoute.progressText.includes("2/4"),
    durable_job_survives_route: normal.jobBeforeRoute.durable === "true" && normal.routeMotion.jobStillVisible,
    skeleton_after_real_300ms_budget: normal.beforeSkeleton && normal.afterBudget.skeletonVisible && normal.refreshComplete.skeletonHidden,
    real_refresh_settles_success: normal.refreshComplete.feedbackState === "success",
    delayed_failure_never_auto_succeeds: normal.delayedSettingsBeforeResponse.feedbackState !== "success"
      && normal.delayedSettingsFailure.feedbackState === "failure",
    reduced_motion_zero_duration: reduced.reduced && reduced.motionDuration === 0 && reduced.activeAnimations === 0,
    unsupported_haptic_silent_degrade: reduced.capability.haptic === false && reduced.unsupportedResult.delivery === "visual_only",
    elapsed_classification_exact: JSON.stringify(reduced.elapsedClasses) === JSON.stringify(["instant", "cached", "skeleton", "staged", "durable"]),
    screenshot_written: normal.screenshotBytes > 10_000,
    only_expected_console_failure: diagnostics.consoleErrors.length === 1
      && diagnostics.consoleErrors[0].includes("503"),
    no_page_errors: diagnostics.pageErrors.length === 0,
    only_expected_http_failure: diagnostics.httpErrors.length === 1
      && diagnostics.httpErrors[0].status === 503
      && new URL(diagnostics.httpErrors[0].url).pathname === "/api/settings/preferences",
    no_external_requests: diagnostics.blockedExternal.length === 0
      && [...diagnostics.requestedOrigins].every((origin) => origin === new URL(baseUrl).origin),
  };
  result = {
    schema: "PFIV025Stage8Phase82BrowserValidationV1",
    status: Object.values(checks).every(Boolean) ? "pass" : "fail",
    contract_id: "PFI-V025-STAGE8-PHASE82-MOTION-FEEDBACK",
    acceptance_id: "ACC-PFI-V025-STAGE8-WHOLE-REVIEW",
    method: "actual_current_worktree_formal_shell_playwright_ephemeral_loopback",
    actual_formal_shell: true,
    financial_data_loaded: false,
    private_values_persisted: false,
    external_network_performed: false,
    finder_used: false,
    checks,
    normal,
    reduced,
    diagnostics: {
      console_errors: diagnostics.consoleErrors,
      page_errors: diagnostics.pageErrors,
      http_errors: diagnostics.httpErrors,
      blocked_external_requests: diagnostics.blockedExternal,
      requested_origin_count: diagnostics.requestedOrigins.size,
    },
  };
} finally {
  await browser.close();
  server.closeAllConnections?.();
  await new Promise((resolve) => server.close(resolve));
}

await writeFile(path.join(outputDir, "browser_validation.json"), `${JSON.stringify(result, null, 2)}\n`, "utf8");
const sanitizer = path.join(webRoot, "tests", "v025", "stage8_phase81_trace_privacy.py");
const sanitized = spawnSync(process.env.PFI_PYTHON || "python3", ["-B", sanitizer, rawTracePath, tracePath], {
  cwd: path.dirname(webRoot), encoding: "utf8",
});
await unlink(rawTracePath).catch(() => {});
if (sanitized.status !== 0) throw new Error(`trace sanitization failed: ${sanitized.stderr || sanitized.stdout}`);
const traceSha256 = createHash("sha256").update(await readFile(tracePath)).digest("hex");
console.log(JSON.stringify({ status: result.status, checks: result.checks, trace_sha256: traceSha256 }));
if (result.status !== "pass") process.exitCode = 2;
