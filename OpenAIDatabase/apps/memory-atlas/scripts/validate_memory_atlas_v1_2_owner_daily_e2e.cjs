#!/usr/bin/env node
"use strict";

const crypto = require("node:crypto");
const fs = require("node:fs");
const http = require("node:http");
const os = require("node:os");
const path = require("node:path");
const { spawn, spawnSync } = require("node:child_process");


const appRoot = path.resolve(__dirname, "..");
const databaseRoot = path.resolve(appRoot, "../..");
const localPort = Number(process.env.MEMORY_ATLAS_R5_OWNER_DAILY_PORT || 4185);
const staticPort = Number(process.env.MEMORY_ATLAS_R5_STATIC_PORT || localPort + 1);
const localUrl = `http://127.0.0.1:${localPort}`;
const staticUrl = `http://127.0.0.1:${staticPort}`;
const outputDir = process.env.MEMORY_ATLAS_R5_OWNER_DAILY_AUDIT_DIR
  ? path.resolve(databaseRoot, process.env.MEMORY_ATLAS_R5_OWNER_DAILY_AUDIT_DIR)
  : fs.mkdtempSync(path.join(os.tmpdir(), "memory-atlas-r5-owner-daily-audit-"));
const browserExecutable = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || findChromiumExecutable();
const expectedStepIds = [
  "sync",
  "analyze",
  "build-atlas",
  "audit",
  "push",
  "proposals",
  "generate-personalization-prompt",
  "deep-explore",
];
const viewports = [
  { name: "desktop-low-height", width: 1470, height: 661 },
  { name: "desktop-standard", width: 1440, height: 900 },
  { name: "mobile", width: 390, height: 844 },
];


function assertCondition(condition, message, details = {}) {
  if (!condition) {
    const error = new Error(message);
    error.details = details;
    throw error;
  }
}


function sha256(value) {
  return crypto.createHash("sha256").update(value).digest("hex");
}


function treeHash(root) {
  const digest = crypto.createHash("sha256");
  const visit = (directory) => {
    for (const entry of fs.readdirSync(directory, { withFileTypes: true }).sort((left, right) => left.name.localeCompare(right.name))) {
      const absolute = path.join(directory, entry.name);
      const relative = path.relative(root, absolute).split(path.sep).join("/");
      digest.update(`${entry.isDirectory() ? "d" : "f"}:${relative}\0`);
      if (entry.isDirectory()) visit(absolute);
      else if (entry.isFile()) digest.update(fs.readFileSync(absolute));
      else digest.update(fs.readlinkSync(absolute));
    }
  };
  visit(root);
  return digest.digest("hex");
}


function findChromiumExecutable() {
  return [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
  ].find((candidate) => fs.existsSync(candidate));
}


function requirePlaywright() {
  try {
    return require("playwright");
  } catch {}
  const pnpmRoot = path.join(os.homedir(), ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm");
  try {
    const candidate = fs.readdirSync(pnpmRoot).filter((entry) => entry.startsWith("playwright@")).sort().at(-1);
    if (candidate) return require(path.join(pnpmRoot, candidate, "node_modules/playwright"));
  } catch {}
  throw new Error("Playwright is not resolvable from project dependencies or Codex bundled runtime");
}


function runFrontendBuild() {
  const result = spawnSync("npm", ["run", "build"], { cwd: appRoot, env: { ...process.env }, encoding: "utf8" });
  assertCondition(result.status === 0, "Current frontend build failed before R5 Owner Daily validation", {
    stdoutTail: String(result.stdout || "").slice(-3000),
    stderrTail: String(result.stderr || "").slice(-3000),
  });
}


function writeJson(filePath, payload) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, JSON.stringify(payload, null, 2) + "\n", "utf8");
}


function fixtureAtlasctlSource() {
  return `#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

args = sys.argv[1:]
app_support = Path(__file__).resolve().parents[2]
call_log = app_support / "owner_daily_fixture_calls.jsonl"
step_id = args[0] if args else ""
if step_id == "analyze":
    step_id = "analyze"
if "--dry-run" not in args:
    print(json.dumps({"status": "FAIL", "dry_run": False, "writes_files": False}, ensure_ascii=False))
    raise SystemExit(2)
with call_log.open("a", encoding="utf-8") as handle:
    handle.write(json.dumps({"step_id": step_id, "args": args}, ensure_ascii=False) + "\\n")
payload = {"status": "PASS", "command": step_id, "dry_run": True, "writes_files": False}
if step_id == "sync":
    payload["source_id"] = "chatgpt"
elif step_id == "analyze":
    payload.update({"stage": "facets", "task_id": "MA-V12-S05P3", "raw_mutation": False, "event_count": 12})
elif step_id == "build-atlas":
    payload["output"] = "data/derived/visualization/memory_atlas.json"
elif step_id == "audit":
    payload.update({"task_id": "MA-V12-S14P2", "raw_mutation": False, "remote_push": False, "gates": [{"gate_id": "fixture"}]})
    marker = app_support / "owner_daily_audit_retry.marker"
    if not marker.exists():
        marker.write_text("fail-once\\n", encoding="utf-8")
        payload["status"] = "FAIL"
        print(json.dumps(payload, ensure_ascii=False))
        raise SystemExit(2)
elif step_id == "push":
    payload.update({"remote_push": False, "github_main_upload": False, "backup_scope_check": "installed_source_copy_no_git"})
elif step_id == "proposals":
    payload.update({"raw_mutation": False, "proposal_count": 2, "proposal_apply_execution": False})
elif step_id == "generate-personalization-prompt":
    payload.update({"raw_mutation": False, "sends_to_chatgpt": False, "targets": ["chatgpt", "codex", "other_agent"]})
elif step_id == "deep-explore":
    payload.update({"raw_mutation": False, "sends_to_chatgpt": False, "opens_browser": False, "mode": "prefill_only"})
else:
    payload["status"] = "FAIL"
    print(json.dumps(payload, ensure_ascii=False))
    raise SystemExit(2)
print(json.dumps(payload, ensure_ascii=False))
`;
}


function prepareFixture() {
  const fixtureRoot = fs.mkdtempSync(path.join(os.tmpdir(), "memory-atlas-r5-owner-daily-"));
  const appSupport = path.join(fixtureRoot, "app-support");
  const sourceRoot = path.join(appSupport, "source");
  const runtimeDir = path.join(appSupport, "runtime");
  const scriptsDir = path.join(sourceRoot, "scripts");
  fs.mkdirSync(scriptsDir, { recursive: true });
  fs.mkdirSync(runtimeDir, { recursive: true });
  for (const script of [
    "memory_atlas_runtime_server.py",
    "memory_atlas_command_bridge.py",
    "memory_atlas_owner_daily.py",
    "memory_atlas_proposal_workflow.py",
  ]) {
    fs.copyFileSync(path.join(databaseRoot, "scripts", script), path.join(scriptsDir, script));
  }
  fs.writeFileSync(path.join(scriptsDir, "atlasctl.py"), fixtureAtlasctlSource(), { encoding: "utf8", mode: 0o755 });
  writeJson(path.join(sourceRoot, "memory_atlas_source_workspace.json"), {
    schema_version: "memory_atlas_source_workspace.v1",
    original_repo_root: databaseRoot,
    installed_git_commit: "r5-browser-fixture",
    purpose: "Temporary installer-shaped R5 Owner Daily browser fixture.",
  });
  fs.cpSync(path.join(appRoot, "dist"), runtimeDir, { recursive: true, preserveTimestamps: true });
  fs.copyFileSync(
    path.join(databaseRoot, "data/derived/visualization/memory_atlas.json"),
    path.join(runtimeDir, "memory_atlas.json"),
  );
  return {
    appSupport,
    callLog: path.join(appSupport, "owner_daily_fixture_calls.jsonl"),
    fixtureRoot,
    runtimeDir,
    sourceRoot,
    sourceHashBefore: treeHash(sourceRoot),
    runtimeHashBefore: treeHash(runtimeDir),
  };
}


function startProcess(command, args, options = {}) {
  const child = spawn(command, args, {
    cwd: options.cwd || databaseRoot,
    env: { ...process.env, ...(options.env || {}) },
    stdio: ["ignore", "pipe", "pipe"],
  });
  const logs = [];
  child.stdout.on("data", (chunk) => logs.push(chunk.toString()));
  child.stderr.on("data", (chunk) => logs.push(chunk.toString()));
  return { child, logs };
}


function httpRequest(url, options = {}, body = "") {
  return new Promise((resolve, reject) => {
    const target = new URL(url);
    const request = http.request(
      {
        hostname: target.hostname,
        port: target.port,
        path: `${target.pathname}${target.search}`,
        method: options.method || "GET",
        headers: options.headers || {},
      },
      (response) => {
        const chunks = [];
        response.on("data", (chunk) => chunks.push(chunk));
        response.on("end", () => resolve({
          body: Buffer.concat(chunks).toString("utf8"),
          headers: response.headers,
          status: response.statusCode || 0,
        }));
      },
    );
    request.setTimeout(options.timeoutMs || 2000, () => request.destroy(new Error(`timeout waiting for ${url}`)));
    request.on("error", reject);
    if (body) request.write(body);
    request.end();
  });
}


async function waitForHttp(url, processHandle, timeoutMs = 30000) {
  const started = Date.now();
  let lastError = null;
  while (Date.now() - started < timeoutMs) {
    if (processHandle.child.exitCode !== null) {
      throw new Error(`Server exited before readiness with code ${processHandle.child.exitCode}: ${processHandle.logs.join("").slice(-3000)}`);
    }
    try {
      const response = await httpRequest(url, { timeoutMs: 1200 });
      if (response.status >= 200 && response.status < 500) return response;
    } catch (error) {
      lastError = error;
    }
    await new Promise((resolve) => setTimeout(resolve, 200));
  }
  throw new Error(`Server did not become ready at ${url}: ${lastError?.message || "unknown"}`);
}


function waitForProcessExit(child, timeoutMs) {
  if (child.exitCode !== null || child.signalCode !== null) return Promise.resolve(true);
  return new Promise((resolve) => {
    let settled = false;
    const finish = (value) => {
      if (settled) return;
      settled = true;
      child.removeListener("exit", onExit);
      clearTimeout(timer);
      resolve(value);
    };
    const onExit = () => finish(true);
    const timer = setTimeout(() => finish(false), timeoutMs);
    child.once("exit", onExit);
    if (child.exitCode !== null || child.signalCode !== null) finish(true);
  });
}


async function stopProcess(processHandle) {
  if (!processHandle || processHandle.child.exitCode !== null) return;
  processHandle.child.kill("SIGTERM");
  await waitForProcessExit(processHandle.child, 2500);
  if (processHandle.child.exitCode === null) {
    processHandle.child.kill("SIGKILL");
    await waitForProcessExit(processHandle.child, 2500);
  }
}


async function closeBrowserWithin(browser, timeoutMs = 4000) {
  if (!browser) return;
  await Promise.race([browser.close().catch(() => undefined), new Promise((resolve) => setTimeout(resolve, timeoutMs))]);
}


async function ownerDailyLayout(page, viewport) {
  await page.setViewportSize({ width: viewport.width, height: viewport.height });
  const result = await page.locator("[data-r5-owner-daily-workspace]").evaluate((backdrop) => {
    const surface = backdrop.querySelector(".owner-daily-workspace-surface");
    const body = backdrop.querySelector(".owner-daily-workspace-body");
    const summary = backdrop.querySelector("[data-r5-owner-daily-summary]");
    const stepList = backdrop.querySelector("[data-r5-owner-daily-step-list]");
    const surfaceBox = surface?.getBoundingClientRect();
    const summaryBox = summary?.getBoundingClientRect();
    const stepListBox = stepList?.getBoundingClientRect();
    const stepOverflow = Array.from(backdrop.querySelectorAll("[data-r5-owner-daily-step]")).filter((item) => item.scrollWidth > item.clientWidth + 1).length;
    return {
      documentClientWidth: document.documentElement.clientWidth,
      documentScrollWidth: document.documentElement.scrollWidth,
      surface: surfaceBox ? { left: surfaceBox.left, right: surfaceBox.right, top: surfaceBox.top, bottom: surfaceBox.bottom } : null,
      bodyClientWidth: body?.clientWidth || 0,
      bodyScrollWidth: body?.scrollWidth || 0,
      summaryBottom: summaryBox?.bottom || 0,
      stepListTop: stepListBox?.top || 0,
      stepOverflow,
    };
  });
  assertCondition(result.surface, `R5 Owner Daily surface missing at ${viewport.name}`, result);
  assertCondition(result.surface.left >= -1 && result.surface.right <= viewport.width + 1, `R5 surface escapes horizontally at ${viewport.name}`, result);
  assertCondition(result.surface.top >= -1 && result.surface.bottom <= viewport.height + 1, `R5 surface escapes vertically at ${viewport.name}`, result);
  assertCondition(result.bodyScrollWidth <= result.bodyClientWidth + 1, `R5 body overflows horizontally at ${viewport.name}`, result);
  assertCondition(result.documentScrollWidth <= result.documentClientWidth + 1, `R5 document overflows horizontally at ${viewport.name}`, result);
  assertCondition(result.summaryBottom <= result.stepListTop + 1, `R5 summary overlaps step list at ${viewport.name}`, result);
  assertCondition(result.stepOverflow === 0, `R5 step cards overflow horizontally at ${viewport.name}`, result);
  const screenshot = `owner-daily-partial-${viewport.name}-${viewport.width}x${viewport.height}.png`;
  await page.screenshot({ path: path.join(outputDir, screenshot), fullPage: false });
  return { ...result, screenshot };
}


async function postProbe(payload, origin = localUrl) {
  const body = JSON.stringify(payload);
  return httpRequest(`${localUrl}/__memory_atlas_owner_daily`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Content-Length": Buffer.byteLength(body),
      Origin: origin,
    },
  }, body);
}


async function main() {
  runFrontendBuild();
  fs.mkdirSync(outputDir, { recursive: true });
  const fixture = prepareFixture();
  const runtimeServer = startProcess(
    "python3",
    [path.join(fixture.sourceRoot, "scripts/memory_atlas_runtime_server.py"), fixture.runtimeDir, String(localPort), "0", "0", fixture.sourceRoot],
    { cwd: fixture.sourceRoot },
  );
  const viteCli = path.join(appRoot, "node_modules/vite/bin/vite.js");
  assertCondition(fs.existsSync(viteCli), "Vite CLI is missing from app node_modules", { viteCli });
  const staticServer = startProcess(process.execPath, [viteCli, "preview", "--host", "127.0.0.1", "--port", String(staticPort), "--strictPort"], { cwd: appRoot });
  let browser = null;
  let staticBrowser = null;
  const status = {
    status: "FAIL",
    phase: "R5_OWNER_DAILY_PRODUCT_ENTRY",
    owner_daily_api_version: "memory_atlas_owner_daily_api.v1_2_r5",
    local_url: localUrl,
    static_url: staticUrl,
    layout: {},
    workflow: {},
    security: {},
    hosted_static: {},
    artifacts: {},
    screenshots: [],
  };

  try {
    await waitForHttp(`${localUrl}/__memory_atlas_runtime_state`, runtimeServer);
    await waitForHttp(staticUrl, staticServer);

    const remoteOrigin = await postProbe({ action: "run" }, "https://evil.example");
    const extraField = await postProbe({ action: "run", argv: ["rm", "-rf", "/"] });
    const unknownStep = await postProbe({ action: "retry", step_id: "audit;rm" });
    assertCondition(remoteOrigin.status === 403, "Remote Owner Daily Origin was not rejected", remoteOrigin);
    assertCondition(extraField.status === 400, "Owner Daily extra argv was not rejected", extraField);
    assertCondition(unknownStep.status === 400, "Unknown Owner Daily retry step was not rejected", unknownStep);
    assertCondition(!fs.existsSync(fixture.callLog), "Rejected probes executed a child process");

    const { chromium } = requirePlaywright();
    browser = await chromium.launch({ headless: true, executablePath: browserExecutable });
    const context = await browser.newContext({ viewport: { width: 1470, height: 661 }, reducedMotion: "reduce" });
    const page = await context.newPage();
    const ownerRequests = [];
    page.on("request", (request) => {
      if (new URL(request.url()).pathname === "/__memory_atlas_owner_daily") {
        ownerRequests.push({ method: request.method(), postData: request.postData() || "" });
      }
    });
    await page.goto(localUrl, { waitUntil: "networkidle" });
    await page.waitForSelector('[data-r5-owner-daily-api-available="true"]');
    assertCondition(await page.locator("[data-s12-p1-command-id]").count() === 6, "R5 changed the exact six-command R3 registry");
    await page.locator("[data-r5-owner-daily-open]").click();
    await page.waitForSelector('[data-r5-owner-daily-workspace="memory_atlas_owner_daily_ui.v1_2_r5"]');
    assertCondition(ownerRequests.length === 0, "Opening Owner Daily triggered execution before explicit start", { ownerRequests });
    await page.locator("[data-r5-owner-daily-start]").click();
    await page.waitForSelector('[data-r5-owner-daily-result-status="PARTIAL_FAILURE"]', { timeout: 30000 });
    assertCondition(await page.locator("[data-r5-owner-daily-step]").count() === 8, "Owner Daily did not render eight ordered step results");
    assertCondition(await page.locator('[data-r5-owner-daily-step="audit"][data-r5-owner-daily-step-status="failed"]').count() === 1, "Audit partial failure is not rendered");
    const failureText = await page.locator('[data-r5-owner-daily-step="audit"] [data-r5-owner-daily-failure]').innerText();
    assertCondition(/[\u4e00-\u9fff]/.test(failureText), "Owner Daily failure is not actionable Chinese", { failureText });
    assertCondition(await page.locator('[data-r5-owner-daily-completed-count="7"]').count() === 1, "Owner Daily partial result does not show 7 completed");
    assertCondition(await page.locator('[data-r5-owner-daily-failed-count="1"]').count() === 1, "Owner Daily partial result does not show 1 failed");

    for (const viewport of viewports) {
      status.layout[viewport.name] = await ownerDailyLayout(page, viewport);
      status.screenshots.push(status.layout[viewport.name].screenshot);
    }
    await page.setViewportSize({ width: 1470, height: 661 });
    await page.locator('[data-r5-owner-daily-retry="audit"]').click();
    await page.waitForSelector('[data-r5-owner-daily-result-status="PASS"]', { timeout: 30000 });
    assertCondition(await page.locator('[data-r5-owner-daily-step="audit"][data-r5-owner-daily-step-status="pass"]').count() === 1, "Audit retry did not merge into the eight-step result");
    assertCondition(await page.locator('[data-r5-owner-daily-completed-count="8"]').count() === 1, "Owner Daily merged result does not show 8 completed");
    assertCondition(await page.locator('[data-r5-owner-daily-failed-count="0"]').count() === 1, "Owner Daily merged result does not show 0 failed");
    await page.locator('[data-r5-owner-daily-step="audit"] details summary').click();
    const machineText = await page.locator('[data-r5-owner-daily-step="audit"] details').innerText();
    assertCondition(machineText.includes("python3 scripts/atlasctl.py audit --dry-run"), "Fixed audit invocation is missing from collapsed machine details", { machineText });
    const hook = await page.evaluate(() => window.__memoryAtlasR5OwnerDaily?.());
    assertCondition(hook?.ownerDailyApiVersion === "memory_atlas_owner_daily_api.v1_2_r5", "R5 browser hook API version is missing", { hook });
    assertCondition(hook?.resultStatus === "PASS" && hook?.completedCount === 8 && hook?.failedCount === 0, "R5 browser hook does not expose merged result", { hook });
    assertCondition(hook?.canonicalRepoMutation === false && hook?.remotePush === false, "R5 browser hook safety boundary failed", { hook });
    const finalScreenshot = "owner-daily-pass-after-fixed-retry.png";
    await page.screenshot({ path: path.join(outputDir, finalScreenshot), fullPage: false });
    status.screenshots.push(finalScreenshot);
    await context.close();
    await browser.close();
    browser = null;

    const requestBodies = ownerRequests.map((request) => JSON.parse(request.postData));
    assertCondition(JSON.stringify(requestBodies) === JSON.stringify([{ action: "run" }, { action: "retry", step_id: "audit" }]), "Browser emitted an unexpected Owner Daily request body", { requestBodies });
    const childCalls = fs.readFileSync(fixture.callLog, "utf8").trim().split("\n").filter(Boolean).map((line) => JSON.parse(line));
    assertCondition(childCalls.length === 9, "Owner Daily did not execute eight steps plus one fixed retry", { childCalls });
    assertCondition(JSON.stringify(childCalls.slice(0, 8).map((row) => row.step_id)) === JSON.stringify(expectedStepIds), "Initial Owner Daily child order changed", { childCalls });
    assertCondition(childCalls[8].step_id === "audit", "Retry executed a step other than audit", { childCalls });

    staticBrowser = await chromium.launch({ headless: true, executablePath: browserExecutable });
    const staticContext = await staticBrowser.newContext({ viewport: { width: 1470, height: 661 }, reducedMotion: "reduce" });
    const staticPage = await staticContext.newPage();
    const staticOwnerRequests = [];
    staticPage.on("request", (request) => {
      if (new URL(request.url()).pathname === "/__memory_atlas_owner_daily") staticOwnerRequests.push(request.method());
    });
    await staticPage.goto(staticUrl, { waitUntil: "networkidle" });
    await staticPage.waitForTimeout(1500);
    const handoff = await staticPage.locator("[data-r5-owner-daily-handoff]").getAttribute("href");
    assertCondition(handoff === "http://127.0.0.1:4177", "Hosted static Owner Daily handoff is not exact", { handoff });
    assertCondition(await staticPage.locator("[data-r5-owner-daily-open]").count() === 0, "Hosted static exposes an executable Owner Daily button");
    assertCondition(await staticPage.locator("[data-r5-owner-daily-workspace]").count() === 0, "Hosted static opened a fake Owner Daily workspace");
    assertCondition(staticOwnerRequests.length === 0, "Hosted static emitted an Owner Daily POST", { staticOwnerRequests });
    const staticScreenshot = "owner-daily-hosted-static-read-only.png";
    await staticPage.screenshot({ path: path.join(outputDir, staticScreenshot), fullPage: false });
    status.screenshots.push(staticScreenshot);
    await staticContext.close();
    await staticBrowser.close();
    staticBrowser = null;

    const auditPath = path.join(fixture.appSupport, "owner_daily_audit.jsonl");
    const auditText = fs.readFileSync(auditPath, "utf8");
    const auditRows = auditText.trim().split("\n").filter(Boolean).map((line) => JSON.parse(line));
    assertCondition(auditRows.length === 2, "Owner Daily audit does not contain run and retry rows", { auditRows });
    assertCondition(JSON.stringify(auditRows.map((row) => row.action)) === JSON.stringify(["run", "retry"]), "Owner Daily audit action order changed", { auditRows });
    assertCondition(!auditText.includes(fixture.sourceRoot) && !auditText.includes("stdout") && !auditText.includes("steps"), "Owner Daily audit contains path or child output");
    const sourceHashAfter = treeHash(fixture.sourceRoot);
    const runtimeHashAfter = treeHash(fixture.runtimeDir);
    assertCondition(sourceHashAfter === fixture.sourceHashBefore, "Owner Daily changed installer source bytes", { before: fixture.sourceHashBefore, after: sourceHashAfter });
    assertCondition(runtimeHashAfter === fixture.runtimeHashBefore, "Owner Daily changed runtime bytes", { before: fixture.runtimeHashBefore, after: runtimeHashAfter });

    status.workflow = {
      initial_status: "PARTIAL_FAILURE",
      initial_completed_count: 7,
      initial_failed_count: 1,
      failed_step_id: "audit",
      retry_status: "PASS",
      merged_completed_count: 8,
      merged_failed_count: 0,
      child_call_count: childCalls.length,
      fixed_retry_only: childCalls[8].step_id === "audit",
      human_conclusion_before_machine_details: true,
    };
    status.security = {
      remote_origin_rejected: remoteOrigin.status === 403,
      extra_argv_rejected: extraField.status === 400,
      unknown_step_rejected: unknownStep.status === 400,
      exact_browser_request_bodies: requestBodies,
      source_unchanged: true,
      runtime_unchanged: true,
      audit_metadata_only: true,
      canonical_repo_mutation: false,
      remote_push: false,
    };
    status.hosted_static = {
      owner_daily_post_count: 0,
      local_handoff: handoff,
      executable_button_exposed: false,
      fake_workspace_opened: false,
    };
    status.artifacts = {
      source_sha256_before: fixture.sourceHashBefore,
      source_sha256_after: sourceHashAfter,
      runtime_sha256_before: fixture.runtimeHashBefore,
      runtime_sha256_after: runtimeHashAfter,
      owner_daily_audit_row_count: auditRows.length,
    };
    status.status = "PASS";
    fs.writeFileSync(path.join(outputDir, "status.json"), JSON.stringify(status, null, 2) + "\n", "utf8");
    process.stdout.write(JSON.stringify(status, null, 2) + "\n");
  } catch (error) {
    status.error = error.message;
    status.details = error.details || {};
    fs.mkdirSync(outputDir, { recursive: true });
    fs.writeFileSync(path.join(outputDir, "status.json"), JSON.stringify(status, null, 2) + "\n", "utf8");
    process.stderr.write(JSON.stringify(status, null, 2) + "\n");
    process.exitCode = 1;
  } finally {
    await stopProcess(runtimeServer);
    await stopProcess(staticServer);
    if (browser) await closeBrowserWithin(browser);
    if (staticBrowser) await closeBrowserWithin(staticBrowser);
    fs.rmSync(fixture.fixtureRoot, { recursive: true, force: true });
  }
}


main().catch((error) => {
  process.stderr.write(`${error.stack || error}\n`);
  process.exitCode = 1;
});
