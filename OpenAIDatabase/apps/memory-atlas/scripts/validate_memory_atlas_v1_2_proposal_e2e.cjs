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
const localPort = Number(process.env.MEMORY_ATLAS_R4_PROPOSAL_PORT || 4183);
const staticPort = Number(process.env.MEMORY_ATLAS_R4_STATIC_PORT || localPort + 1);
const localUrl = `http://127.0.0.1:${localPort}`;
const staticUrl = `http://127.0.0.1:${staticPort}`;
const outputDir = process.env.MEMORY_ATLAS_R4_PROPOSAL_AUDIT_DIR
  ? path.resolve(databaseRoot, process.env.MEMORY_ATLAS_R4_PROPOSAL_AUDIT_DIR)
  : fs.mkdtempSync(path.join(os.tmpdir(), "memory-atlas-r4-proposal-audit-"));
const browserExecutable = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || findChromiumExecutable();
const proposalIds = {
  success: "proposal_success",
  failure: "proposal_failure",
  raw: "proposal_raw_target",
};
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


function findChromiumExecutable() {
  const candidates = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
  ];
  return candidates.find((candidate) => fs.existsSync(candidate));
}


function requirePlaywright() {
  try {
    return require("playwright");
  } catch {}
  const pnpmRoot = path.join(
    os.homedir(),
    ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm",
  );
  try {
    const candidate = fs.readdirSync(pnpmRoot)
      .filter((entry) => entry.startsWith("playwright@"))
      .sort()
      .at(-1);
    if (candidate) return require(path.join(pnpmRoot, candidate, "node_modules/playwright"));
  } catch {}
  throw new Error("Playwright is not resolvable from project dependencies or Codex bundled runtime");
}


function runFrontendBuild() {
  const result = spawnSync("npm", ["run", "build"], {
    cwd: appRoot,
    env: { ...process.env },
    encoding: "utf8",
  });
  assertCondition(result.status === 0, "Current frontend build failed before R4 proposal validation", {
    stdoutTail: String(result.stdout || "").slice(-3000),
    stderrTail: String(result.stderr || "").slice(-3000),
  });
}


function copyDirectory(relativePath, sourceRoot) {
  const source = path.join(databaseRoot, relativePath);
  const target = path.join(sourceRoot, relativePath);
  assertCondition(fs.existsSync(source), `Required R4 fixture source is missing: ${relativePath}`);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.cpSync(source, target, { recursive: true, preserveTimestamps: true });
}


function writeJson(filePath, payload) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, JSON.stringify(payload, null, 2) + "\n", "utf8");
}


function narrator(targetFile) {
  return {
    what_changed_zh: "改了什么：替换一个精确目标文件。",
    why_changed_zh: "为什么改：验证真实人类授权、应用、验证和回滚闭环。",
    affected_surfaces_zh: `影响什么：仅影响 ${targetFile}。`,
    how_to_verify_zh: "如何验证：运行固定 UTF-8 和 JSON document 验证器。",
    how_to_rollback_zh: "如何回滚：恢复 apply 前保存的完整文件字节。",
  };
}


function proposalBundle({ proposalId, targetFile, expectedSha, content, targetType = "config" }) {
  return {
    schema_version: "memory_atlas_apply_ready_proposal.v1_2_r4",
    proposal_id: proposalId,
    current_state: "pending_human_review",
    target_type: targetType,
    risk_level: "low",
    expires_at: "2099-08-07T08:18:30Z",
    action_half_life: "this_week",
    human_reason_zh: "用于 R4 真实浏览器授权闭环验收。",
    narrator: narrator(targetFile),
    operations: [
      {
        operation: "replace_text",
        target_file: targetFile,
        expected_sha256: expectedSha,
        content,
      },
    ],
    validation_ids: ["utf8_nonempty", "json_document"],
    rollback_plan_zh: "恢复事务快照并核对原始 SHA-256；raw 文件不参与回滚。",
  };
}


function prepareFixture() {
  const fixtureRoot = fs.mkdtempSync(path.join(os.tmpdir(), "memory-atlas-r4-proposal-"));
  const appSupport = path.join(fixtureRoot, "app-support");
  const sourceRoot = path.join(appSupport, "source");
  const runtimeDir = path.join(appSupport, "runtime");
  fs.mkdirSync(sourceRoot, { recursive: true });
  fs.mkdirSync(runtimeDir, { recursive: true });
  for (const relativePath of ["scripts", "config", "data", "skills", "机器治理/运行门禁", "人类可读"]) {
    copyDirectory(relativePath, sourceRoot);
  }
  writeJson(path.join(sourceRoot, "memory_atlas_source_workspace.json"), {
    schema_version: "memory_atlas_source_workspace.v1",
    original_repo_root: databaseRoot,
    installed_git_commit: "r4-browser-fixture",
    purpose: "Temporary installer-shaped R4 proposal browser fixture.",
  });
  fs.cpSync(path.join(appRoot, "dist"), runtimeDir, { recursive: true, preserveTimestamps: true });
  fs.copyFileSync(
    path.join(sourceRoot, "data/derived/visualization/memory_atlas.json"),
    path.join(runtimeDir, "memory_atlas.json"),
  );

  const successTarget = path.join(sourceRoot, "config/r4_acceptance/success.json");
  const failureTarget = path.join(sourceRoot, "config/r4_acceptance/failure.json");
  const rawSentinel = path.join(sourceRoot, "data/raw/r4-sentinel.json");
  const successBefore = Buffer.from('{"value":"before-success"}\n', "utf8");
  const failureBefore = Buffer.from('{"value":"before-failure"}\n', "utf8");
  const rawBefore = Buffer.from('{"raw":"must-not-change"}\n', "utf8");
  fs.mkdirSync(path.dirname(successTarget), { recursive: true });
  fs.mkdirSync(path.dirname(rawSentinel), { recursive: true });
  fs.writeFileSync(successTarget, successBefore);
  fs.writeFileSync(failureTarget, failureBefore);
  fs.writeFileSync(rawSentinel, rawBefore);

  const bundles = [
    proposalBundle({
      proposalId: proposalIds.success,
      targetFile: "config/r4_acceptance/success.json",
      expectedSha: sha256(successBefore),
      content: '{"value":"after-success","approved_change":true}\n',
    }),
    proposalBundle({
      proposalId: proposalIds.failure,
      targetFile: "config/r4_acceptance/failure.json",
      expectedSha: sha256(failureBefore),
      content: "not-json\n",
    }),
    proposalBundle({
      proposalId: proposalIds.raw,
      targetFile: "data/raw/r4-sentinel.json",
      expectedSha: sha256(rawBefore),
      content: '{"raw":"changed"}\n',
    }),
  ];
  for (const bundle of bundles) {
    writeJson(path.join(sourceRoot, "data/derived/proposals/apply_ready", `${bundle.proposal_id}.json`), bundle);
  }
  return {
    appSupport,
    failureBefore,
    failureTarget,
    fixtureRoot,
    rawBefore,
    rawSentinel,
    runtimeDir,
    sourceRoot,
    successBefore,
    successTarget,
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


async function stopProcess(processHandle) {
  if (!processHandle || processHandle.child.exitCode !== null) return;
  processHandle.child.kill("SIGTERM");
  await waitForProcessExit(processHandle.child, 2500);
  if (processHandle.child.exitCode === null) {
    processHandle.child.kill("SIGKILL");
    await waitForProcessExit(processHandle.child, 2500);
  }
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


async function closeBrowserWithin(browser, timeoutMs = 4000) {
  if (!browser) return;
  await Promise.race([
    browser.close().catch(() => undefined),
    new Promise((resolve) => setTimeout(resolve, timeoutMs)),
  ]);
}


async function openProposalWorkspace(page) {
  await page.locator('[data-s12-p1-command-id="view_pending_proposals"]').scrollIntoViewIfNeeded();
  await page.locator('[data-s12-p1-command-id="view_pending_proposals"]').click();
  await page.locator('[data-r3-command-execute="view_pending_proposals"]').click();
  await page.waitForSelector('[data-r4-proposal-workspace="memory_atlas_proposal_workflow.v1_2_r4"]', { timeout: 30000 });
}


async function proposalLayout(page, viewport) {
  await page.setViewportSize({ width: viewport.width, height: viewport.height });
  const result = await page.locator("[data-r4-proposal-workspace]").evaluate((dialog) => {
    const box = dialog.getBoundingClientRect();
    const surface = dialog.querySelector(".proposal-workspace-surface");
    const body = dialog.querySelector(".proposal-workspace-body");
    const surfaceBox = surface?.getBoundingClientRect();
    return {
      dialog: { left: box.left, right: box.right, top: box.top, bottom: box.bottom, width: box.width, height: box.height },
      surface: surfaceBox ? { left: surfaceBox.left, right: surfaceBox.right, top: surfaceBox.top, bottom: surfaceBox.bottom, width: surfaceBox.width, height: surfaceBox.height } : null,
      bodyClientWidth: body?.clientWidth || 0,
      bodyScrollWidth: body?.scrollWidth || 0,
      surfaceClientHeight: surface?.clientHeight || 0,
      surfaceScrollHeight: surface?.scrollHeight || 0,
    };
  });
  assertCondition(result.surface, `R4 proposal surface missing at ${viewport.name}`, result);
  assertCondition(result.surface.left >= -1 && result.surface.right <= viewport.width + 1, `R4 proposal surface escapes horizontally at ${viewport.name}`, result);
  assertCondition(result.surface.top >= -1 && result.surface.bottom <= viewport.height + 1, `R4 proposal surface escapes vertically at ${viewport.name}`, result);
  assertCondition(result.bodyScrollWidth <= result.bodyClientWidth + 1, `R4 proposal body overflows horizontally at ${viewport.name}`, result);
  const screenshot = `proposal-review-${viewport.name}-${viewport.width}x${viewport.height}.png`;
  await page.screenshot({ path: path.join(outputDir, screenshot), fullPage: false });
  return { ...result, screenshot };
}


async function selectProposal(page, proposalId) {
  const selector = `[data-r4-proposal-id="${proposalId}"]`;
  await page.locator(selector).scrollIntoViewIfNeeded();
  await page.locator(selector).click();
  await page.waitForFunction((id) => document.querySelector("[data-r4-selected-proposal]")?.getAttribute("data-r4-selected-proposal") === id, proposalId);
}


async function main() {
  runFrontendBuild();
  fs.mkdirSync(outputDir, { recursive: true });
  const fixture = prepareFixture();
  const runtimeServer = startProcess(
    "python3",
    [
      path.join(fixture.sourceRoot, "scripts/memory_atlas_runtime_server.py"),
      fixture.runtimeDir,
      String(localPort),
      "0",
      "0",
      fixture.sourceRoot,
    ],
    { cwd: fixture.sourceRoot },
  );
  const viteCli = path.join(appRoot, "node_modules/vite/bin/vite.js");
  assertCondition(fs.existsSync(viteCli), "Vite CLI is missing from app node_modules", { viteCli });
  const staticServer = startProcess(
    process.execPath,
    [viteCli, "preview", "--host", "127.0.0.1", "--port", String(staticPort), "--strictPort"],
    { cwd: appRoot },
  );
  let browser = null;
  let staticBrowser = null;
  const status = {
    status: "FAIL",
    phase: "R4_PROPOSAL_APPROVAL_APPLY_ROLLBACK_WORKFLOW",
    proposal_api_version: "memory_atlas_proposal_api.v1_2_r4",
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

    const unauthorizedBody = JSON.stringify({
      action: "approve_apply",
      proposal_id: proposalIds.success,
      review_token: "not-issued",
      confirmation: `授权应用 ${proposalIds.success}`,
    });
    const unauthorized = await httpRequest(`${localUrl}/__memory_atlas_proposal_action`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Content-Length": Buffer.byteLength(unauthorizedBody),
        Origin: localUrl,
      },
    }, unauthorizedBody);
    assertCondition(unauthorized.status === 400, "Unauthorized proposal apply did not fail closed", unauthorized);
    assertCondition(sha256(fs.readFileSync(fixture.successTarget)) === sha256(fixture.successBefore), "Unauthorized probe changed success target");

    const remoteOrigin = await httpRequest(`${localUrl}/__memory_atlas_proposal_action`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Content-Length": Buffer.byteLength(unauthorizedBody),
        Origin: "https://evil.example",
      },
    }, unauthorizedBody);
    assertCondition(remoteOrigin.status === 403, "Remote proposal Origin was not rejected", remoteOrigin);

    const extraBody = JSON.stringify({ ...JSON.parse(unauthorizedBody), target_file: "data/raw/r4-sentinel.json" });
    const extraField = await httpRequest(`${localUrl}/__memory_atlas_proposal_action`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Content-Length": Buffer.byteLength(extraBody),
        Origin: localUrl,
      },
    }, extraBody);
    assertCondition(extraField.status === 400, "Extra proposal action field was not rejected", extraField);

    const { chromium } = requirePlaywright();
    browser = await chromium.launch({ headless: true, executablePath: browserExecutable });
    const context = await browser.newContext({ viewport: { width: 1470, height: 661 }, reducedMotion: "reduce" });
    const page = await context.newPage();
    const localRequests = [];
    page.on("request", (request) => {
      const pathname = new URL(request.url()).pathname;
      if (pathname === "/__memory_atlas_command" || pathname === "/__memory_atlas_proposal_action") {
        localRequests.push({ method: request.method(), pathname, postData: request.postData() || "" });
      }
    });
    await page.goto(localUrl, { waitUntil: "networkidle" });
    await openProposalWorkspace(page);

    const proposalCount = await page.locator("[data-r4-proposal-id]").count();
    assertCondition(proposalCount >= 4, "R4 proposal workspace did not render apply-ready and review-only proposals", { proposalCount });
    await selectProposal(page, proposalIds.success);
    for (const field of ["what_changed_zh", "why_changed_zh", "affected_surfaces_zh", "how_to_verify_zh", "how_to_rollback_zh"]) {
      const text = await page.locator(`[data-r4-diff-section="${field}"]`).innerText();
      assertCondition(/[\u4e00-\u9fff]/.test(text), `R4 Chinese diff section missing: ${field}`, { text });
    }
    assertCondition(await page.locator('[data-r4-target-file="config/r4_acceptance/success.json"]').count() === 1, "Exact proposal target file is not rendered");
    assertCondition(await page.locator('[data-r4-validation-id="json_document"]').count() === 1, "Fixed JSON validator is not rendered");
    assertCondition(await page.locator(`[data-r4-apply="${proposalIds.success}"]`).isDisabled(), "Apply is enabled before human acknowledgement");

    for (const viewport of viewports) {
      status.layout[viewport.name] = await proposalLayout(page, viewport);
      status.screenshots.push(status.layout[viewport.name].screenshot);
    }
    await page.setViewportSize({ width: 1470, height: 661 });

    await page.locator("[data-r4-apply-ack]").check();
    await page.locator(`[data-r4-apply="${proposalIds.success}"]`).click();
    await page.waitForFunction((id) => document.querySelector(`[data-r4-action-result="${id}"]`)?.getAttribute("data-r4-action-state") === "committed", proposalIds.success);
    const successAfterSha = sha256(fs.readFileSync(fixture.successTarget));
    assertCondition(successAfterSha !== sha256(fixture.successBefore), "Authorized apply did not change the success target");

    await page.getByRole("button", { name: "关闭提案复核" }).click();
    await openProposalWorkspace(page);
    await selectProposal(page, proposalIds.success);
    assertCondition(
      await page.locator(`[data-r4-persisted-transaction][data-r4-transaction-proposal="${proposalIds.success}"]`).count() === 1,
      "Committed transaction is not available after reopening the proposal workspace",
    );
    const persistedRollbackScreenshot = "proposal-persisted-rollback-after-reopen.png";
    await page.screenshot({ path: path.join(outputDir, persistedRollbackScreenshot), fullPage: false });
    status.screenshots.push(persistedRollbackScreenshot);
    assertCondition(await page.locator("[data-r4-rollback]").isDisabled(), "Rollback is enabled before separate acknowledgement");
    await page.locator("[data-r4-rollback-ack]").check();
    await page.locator("[data-r4-rollback]").click();
    await page.waitForFunction(() => document.querySelector("[data-r4-action-result]")?.getAttribute("data-r4-action-state") === "rolled_back_by_human");
    assertCondition(sha256(fs.readFileSync(fixture.successTarget)) === sha256(fixture.successBefore), "Manual rollback did not restore success target bytes");

    await selectProposal(page, proposalIds.failure);
    await page.locator("[data-r4-apply-ack]").check();
    await page.locator(`[data-r4-apply="${proposalIds.failure}"]`).click();
    await page.waitForFunction((id) => document.querySelector(`[data-r4-action-result="${id}"]`)?.getAttribute("data-r4-action-state") === "rollback_or_needs_revision", proposalIds.failure);
    assertCondition(sha256(fs.readFileSync(fixture.failureTarget)) === sha256(fixture.failureBefore), "Validation failure did not restore exact target bytes");

    await selectProposal(page, proposalIds.raw);
    assertCondition(await page.locator("[data-r4-review-only-reason]").count() === 1, "Raw proposal is not rendered as review-only");
    assertCondition(await page.locator(`[data-r4-apply="${proposalIds.raw}"]`).count() === 0, "Raw proposal exposes an apply control");
    assertCondition(sha256(fs.readFileSync(fixture.rawSentinel)) === sha256(fixture.rawBefore), "Raw sentinel changed during proposal workflow");

    const hook = await page.evaluate(() => window.__memoryAtlasR4ProposalWorkflow?.());
    assertCondition(hook?.proposalApiVersion === "memory_atlas_proposal_api.v1_2_r4", "R4 browser hook does not expose proposal API version", { hook });
    assertCondition(hook?.rawMutation === false && hook?.canonicalRepoMutation === false, "R4 browser hook safety boundary failed", { hook });
    const finalScreenshot = "proposal-workflow-final-desktop-low.png";
    await page.screenshot({ path: path.join(outputDir, finalScreenshot), fullPage: false });
    status.screenshots.push(finalScreenshot);
    await context.close();
    await browser.close();
    browser = null;

    staticBrowser = await chromium.launch({ headless: true, executablePath: browserExecutable });
    const staticContext = await staticBrowser.newContext({ viewport: { width: 1470, height: 661 }, reducedMotion: "reduce" });
    const staticPage = await staticContext.newPage();
    const staticRequests = [];
    staticPage.on("request", (request) => {
      const pathname = new URL(request.url()).pathname;
      if (pathname === "/__memory_atlas_command" || pathname === "/__memory_atlas_proposal_action") {
        staticRequests.push({ method: request.method(), pathname });
      }
    });
    await staticPage.goto(staticUrl, { waitUntil: "networkidle" });
    await staticPage.waitForTimeout(1500);
    await staticPage.locator('[data-s12-p1-command-id="view_pending_proposals"]').click();
    await staticPage.locator('[data-r3-command-execute="view_pending_proposals"]').click();
    await staticPage.waitForSelector('[data-r3-command-result-status="local_required"]');
    const handoff = await staticPage.locator('[data-r3-command-result-status="local_required"] a').getAttribute("href");
    assertCondition(handoff === "http://127.0.0.1:4177", "Hosted static handoff is not exact", { handoff });
    assertCondition(staticRequests.length === 0, "Hosted static emitted a command or proposal action request", { staticRequests });
    assertCondition(await staticPage.locator("[data-r4-proposal-workspace]").count() === 0, "Hosted static opened a fake proposal workspace");
    const staticScreenshot = "proposal-hosted-static-read-only.png";
    await staticPage.screenshot({ path: path.join(outputDir, staticScreenshot), fullPage: false });
    status.screenshots.push(staticScreenshot);
    await staticContext.close();
    await staticBrowser.close();
    staticBrowser = null;

    const auditPath = path.join(fixture.appSupport, "proposal_audit.jsonl");
    const auditRows = fs.readFileSync(auditPath, "utf8").trim().split("\n").filter(Boolean).map((line) => JSON.parse(line));
    const auditText = fs.readFileSync(auditPath, "utf8");
    assertCondition(auditRows.length === 3, "Proposal audit does not contain apply, manual rollback and failed-validation rows", { auditRows });
    assertCondition(!auditText.includes(fixture.sourceRoot) && !auditText.includes("after-success"), "Proposal audit contains absolute path or file content");

    status.workflow = {
      proposal_count: proposalCount,
      chinese_diff_section_count: 5,
      authorized_apply_real_file_change: true,
      persisted_rollback_visible_after_reopen: true,
      manual_rollback_exact_restore: true,
      validation_failure_automatic_rollback: true,
      raw_proposal_review_only: true,
      state_sequences: {
        success: ["pending_human_review", "approved_by_human", "applying", "applied", "validated", "committed", "rolled_back_by_human"],
        failure: ["pending_human_review", "approved_by_human", "applying", "applied", "failed_validation", "rollback_or_needs_revision"],
      },
    };
    status.security = {
      unauthorized_apply_rejected: unauthorized.status === 400,
      remote_origin_rejected: remoteOrigin.status === 403,
      extra_fields_rejected: extraField.status === 400,
      raw_sentinel_unchanged: true,
      proposal_action_post_count: localRequests.filter((item) => item.pathname === "/__memory_atlas_proposal_action").length,
      command_post_count: localRequests.filter((item) => item.pathname === "/__memory_atlas_command").length,
      audit_metadata_only: true,
      canonical_repo_mutation: false,
      remote_push: false,
    };
    status.hosted_static = {
      command_or_proposal_post_count: 0,
      local_handoff: "http://127.0.0.1:4177",
      fake_workspace_opened: false,
    };
    status.artifacts = {
      success_target_restored: sha256(fs.readFileSync(fixture.successTarget)) === sha256(fixture.successBefore),
      failure_target_restored: sha256(fs.readFileSync(fixture.failureTarget)) === sha256(fixture.failureBefore),
      raw_target_unchanged: sha256(fs.readFileSync(fixture.rawSentinel)) === sha256(fixture.rawBefore),
      transaction_count: fs.readdirSync(path.join(fixture.appSupport, "proposal_transactions"), { withFileTypes: true }).filter((item) => item.isDirectory()).length,
      audit_row_count: auditRows.length,
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
